from pydantic import BaseModel, EmailStr


class BoardCreateRequest(BaseModel):
    name: str


class BoardSummary(BaseModel):
    id: int
    name: str
    owner_id: int
    role: str  # caller's role on this board


class BoardMemberInfo(BaseModel):
    user_id: int
    email: str
    role: str


class BoardDetail(BaseModel):
    id: int
    name: str
    owner_id: int
    role: str
    members: list[BoardMemberInfo]


class UserSummary(BaseModel):
    id: int
    email: str


class AddMemberRequest(BaseModel):
    email: EmailStr
