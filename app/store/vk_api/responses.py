from dataclasses import dataclass


@dataclass
class VKUser:
    id: int
    first_name: str
    last_name: str
    sex: int


@dataclass
class VKGroup:
    id: int
    name: str


@dataclass(init=False)
class ConversationMembersResponse:
    n_users: int
    admin_ids: list[int]
    users: list[VKUser]
    groups: list[VKGroup]

    def __init__(self, data: dict):
        response = data["response"]
        self.n_users = response["count"]

        self.admin_ids = [i["member_id"] for i in response["items"]]

        self.users = []
        for user in response["profiles"]:
            self.users.append(VKUser(id=user["id"],
                                     first_name=user["first_name"],
                                     last_name=user["last_name"],
                                     sex=user["sex"]))

        self.groups = []
        for group in response["groups"]:
            self.groups.append(VKGroup(id=group["id"],
                                       name=group["name"]))
