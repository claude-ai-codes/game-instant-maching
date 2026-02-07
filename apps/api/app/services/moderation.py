from fastapi import HTTPException, status

from app.utils.ng_words import contains_ng_word, contains_url


def check_content(text: str, field_name: str = "content") -> None:
    if contains_ng_word(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} contains prohibited words",
        )
    if contains_url(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must not contain URLs",
        )
