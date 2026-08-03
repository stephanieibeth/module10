# main.py

import logging
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.operations import add, divide, multiply, subtract
from app.schemas.base import UserCreate
from app.schemas.calculation import (
    CalculationCreate,
    CalculationResponse,
    CalculationUpdate,
)
from app.schemas.user import Token, UserLogin, UserResponse


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title="FastAPI Calculator",
    description="Calculator API with user authentication and calculation history",
    version="12.0.0",
)


# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Setup static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------------------------------------
# Existing calculator schemas
# ---------------------------------------------------------------------------

class OperationRequest(BaseModel):
    """Request model for two-number calculator operations."""

    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator("a", "b")
    @classmethod
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Both a and b must be numbers.")
        return value


class OperationResponse(BaseModel):
    """Response model for calculator operations."""

    result: float = Field(..., description="The result of the operation")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return application errors in a consistent JSON format."""

    logger.error(
        "HTTPException on %s: %s",
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """Return Pydantic validation errors in a readable format."""

    error_messages = "; ".join(
        f"{error['loc'][-1]}: {error['msg']}"
        for error in exc.errors()
    )

    logger.error(
        "ValidationError on %s: %s",
        request.url.path,
        error_messages,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": error_messages},
    )


# ---------------------------------------------------------------------------
# User routes
# ---------------------------------------------------------------------------

@app.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    The password is validated and securely hashed before it is stored.
    Duplicate usernames and email addresses are rejected.
    """

    try:
        new_user = User.register(
            db=db,
            user_data=user_data.model_dump(),
        )

        db.commit()
        db.refresh(new_user)

        return new_user

    except ValueError as exc:
        db.rollback()
        error_message = str(exc)

        if "already exists" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error during user registration")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to register user",
        ) from exc


@app.post(
    "/users/login",
    response_model=Token,
    tags=["Users"],
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.

    Users may log in with either their username or email address.
    """

    token = User.authenticate(
        db=db,
        username=login_data.username,
        password=login_data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


# ---------------------------------------------------------------------------
# Calculation BREAD routes
# ---------------------------------------------------------------------------

@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Calculations"],
)
def create_calculation(
    calculation_data: CalculationCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new calculation.

    The calculation factory creates the correct SQLAlchemy subclass based
    on the requested calculation type.
    """

    user = (
        db.query(User)
        .filter(User.id == calculation_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        calculation = Calculation.create(
            calculation_type=calculation_data.type.value,
            user_id=calculation_data.user_id,
            inputs=calculation_data.inputs,
        )

        calculation.result = calculation.get_result()

        db.add(calculation)
        db.commit()
        db.refresh(calculation)

        return calculation

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while creating calculation")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create calculation",
        ) from exc


@app.get(
    "/calculations",
    response_model=list[CalculationResponse],
    tags=["Calculations"],
)
def browse_calculations(
    db: Session = Depends(get_db),
):
    """Browse all calculations stored in the database."""

    return (
        db.query(Calculation)
        .order_by(Calculation.created_at.desc())
        .all()
    )


@app.get(
    "/calculations/{calculation_id}",
    response_model=CalculationResponse,
    tags=["Calculations"],
)
def read_calculation(
    calculation_id: UUID,
    db: Session = Depends(get_db),
):
    """Read one calculation by its UUID."""

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calculation_id)
        .first()
    )

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    return calculation


@app.put(
    "/calculations/{calculation_id}",
    response_model=CalculationResponse,
    tags=["Calculations"],
)
def update_calculation(
    calculation_id: UUID,
    calculation_data: CalculationUpdate,
    db: Session = Depends(get_db),
):
    """
    Edit an existing calculation.

    The calculation type remains unchanged. Updating the inputs automatically
    recalculates and stores the result.
    """

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calculation_id)
        .first()
    )

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    update_data = calculation_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided",
        )

    try:
        if "inputs" in update_data:
            new_inputs = update_data["inputs"]

            if calculation.type == "division" and any(
                value == 0 for value in new_inputs[1:]
            ):
                raise ValueError("Cannot divide by zero")

            calculation.inputs = new_inputs
            calculation.result = calculation.get_result()

        db.commit()
        db.refresh(calculation)

        return calculation

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while updating calculation")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update calculation",
        ) from exc


@app.delete(
    "/calculations/{calculation_id}",
    status_code=status.HTTP_200_OK,
    tags=["Calculations"],
)
def delete_calculation(
    calculation_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete one calculation by its UUID."""

    calculation = (
        db.query(Calculation)
        .filter(Calculation.id == calculation_id)
        .first()
    )

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    try:
        db.delete(calculation)
        db.commit()

        return {
            "message": "Calculation deleted successfully",
            "calculation_id": str(calculation_id),
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Unexpected error while deleting calculation")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete calculation",
        ) from exc


# ---------------------------------------------------------------------------
# Existing web page and calculator routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Application"])
async def read_root(request: Request):
    """Serve the calculator HTML page."""

    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )

@app.get("/register", tags=["Authentication"])
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request},
    )


@app.get("/login", tags=["Authentication"])
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


@app.post(
    "/add",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["Basic Calculator"],
)
async def add_route(operation: OperationRequest):
    """Add two numbers."""

    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)

    except Exception as exc:
        logger.error("Add Operation Error: %s", str(exc))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post(
    "/subtract",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["Basic Calculator"],
)
async def subtract_route(operation: OperationRequest):
    """Subtract two numbers."""

    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)

    except Exception as exc:
        logger.error("Subtract Operation Error: %s", str(exc))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post(
    "/multiply",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["Basic Calculator"],
)
async def multiply_route(operation: OperationRequest):
    """Multiply two numbers."""

    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)

    except Exception as exc:
        logger.error("Multiply Operation Error: %s", str(exc))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@app.post(
    "/divide",
    response_model=OperationResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["Basic Calculator"],
)
async def divide_route(operation: OperationRequest):
    """Divide two numbers."""

    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)

    except ValueError as exc:
        logger.error("Divide Operation Error: %s", str(exc))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Divide Operation Internal Error")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from exc


# ---------------------------------------------------------------------------
# Run application
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )