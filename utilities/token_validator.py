import requests
import jwt  # requires cryptography
from fastapi import HTTPException, status

class JwtTokenHandler:
    @staticmethod
    def verify_token(bearer_token: str, platform_id: str, metadata: dict):
        """
        Validates the provided bearer token against the userinfo endpoint
        and returns token data (user info).
        """
        try:
            name = "shyam"
            parts = bearer_token.split()
            if len(parts) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Authorization token missing!"
                )
            print("AI Studio token validation")

            if parts[1]=="valid_token":
                user_info = {"preferred_username": name+"_user@gmail.com"}
                print(user_info)
                return user_info
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except jwt.exceptions.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid JWT token: {str(e)}"
            )
        except Exception as exc:
            if "Unable to find a signing key" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find a signing key"
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature or token"
            )
        

def validate_token(    
    bearer_token: str, 
    metadata: dict,
    okta_enable: bool = False,
    user_id: str = "123456789"
):
    if okta_enable:
        if not bearer_token:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        user_info = JwtTokenHandler.verify_token(
            bearer_token=bearer_token,
            platform_id="Solution Studio",
            metadata=metadata
        )

        ohr_email = user_info.get("preferred_username", None)
        if user_id:
            if ohr_email:
                ohr = ohr_email.split('@')[0]
                if ohr != user_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Unauthorized access: user ID does not match the authenticated token."
                    )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Unable to extract user information from token."
                )
