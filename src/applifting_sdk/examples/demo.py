import asyncio
import uuid
import os
from http.client import responses

from dotenv import load_dotenv


from applifting_sdk import AppliftingSDKClient, RegisterProductRequest, RegisterProductResponse, OfferResponse
from applifting_sdk.exceptions import AppliftSDKError

load_dotenv("../../../.env")

refresh_token = os.environ.get("REFRESH_TOKEN")


async def main():

    async with AppliftingSDKClient(refresh_token=refresh_token) as client:

        id = uuid.uuid4()
        name = "test_product"
        description = f"This is test product with uuid: {id}"

        product_to_create: RegisterProductRequest = RegisterProductRequest(id=id, name="123", description=description)
        try:
            response: RegisterProductResponse = await client.products.register_product(product_to_create)
            print(response.id)

            response: list[OfferResponse] = await client.offers.get_offers(product_id=response.id)

            for offer in response:
                print("___________")
                print(offer.id)
                print(offer.items_in_stock)
                print(offer.price)


        except AppliftSDKError as e:
            print(e)




if __name__ == "__main__":
    asyncio.run(main())
