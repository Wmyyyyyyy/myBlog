from fastapi import HTTPException, status

class UserAlreadyExists(HTTPException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class InvalidCredentials(HTTPException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class EmailNotVerified(HTTPException):
    def __init__(self, detail: str = "Email not verified"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
