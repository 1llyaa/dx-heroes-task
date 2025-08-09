import asyncio
import uuid
import os
from http.client import responses

from dotenv import load_dotenv


from applift_sdk import AppliftClient, RegisterProductRequest

load_dotenv("../../../.env")

refresh_token = os.environ.get("REFRESH_TOKEN")


async def main():
    print(f"This is refresh token: {refresh_token}")

    async with AppliftClient(refresh_token=refresh_token) as client:

        id = uuid.uuid4()
        name = "test_product"
        description = f"This is test product with uuid: {id}"

        print(f"This is id: {id}")
        print(f"This is name: {name}")
        print(f"This is description: {description}")

        product_to_create: RegisterProductRequest = RegisterProductRequest(id=id, name=name, description=description)
        response = await client.products.register_product(product=product_to_create)
    print(response)
    return response


if __name__ == "__main__":
    asyncio.run(main())
