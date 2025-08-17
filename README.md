
# Applifting Python SDK

A fully asynchronous Python SDK for the [Applifting API](https://python.exercise.applifting.cz/).  
This library handles authentication, token caching, and provides easy-to-use resource clients for Products and Offers.

## ✨ Features

- 🔑 **Automatic token management** — Uses a long-lived refresh token to obtain access tokens.
- 📦 **Products API** — Register and manage products.
- 💰 **Offers API** — Fetch offers for your products.
- 💾 **Token caching** — Avoids unnecessary token requests by storing tokens locally.
- 🛡 **Meaningful exceptions** — Built-in error handling for common API and network errors.
- 🧪 **Typed models** — Pydantic-based request/response validation.

---

## 📦 Installation

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ applifting-sdk-1llyaa==1.0.2
````

Or install from source:

```bash
git clone https://github.com/yourusername/applifting-sdk.git
cd applifting-sdk
pip install -e .
```

---

## 🔧 Configuration

The SDK uses environment variables for configuration. Create a `.env` file in your project root:

```env
REFRESH_TOKEN=your-refresh-token
```

Load environment variables in your code:

```python
from dotenv import load_dotenv

load_dotenv()
```

---

## 🚀 Quick Start

```python
import asyncio
import os
from dotenv import load_dotenv
from applifting_sdk import AppliftingClient, RegisterProductRequest

load_dotenv()

async def main():
    async with AppliftingClient(refresh_token=os.environ["REFRESH_TOKEN"]) as client:
        # Register a product
        product = RegisterProductRequest(
            id="5af8e183-ddb1-4e09-9579-4581b2e67b47",
            name="Test Product",
            description="This is a test product."
        )
        registered = await client.products.register_product(product)
        print("Registered:", registered)

        # Fetch offers for the product
        offers = await client.offers.get_offers(product_id=product.id)
        print("Offers:", offers)

asyncio.run(main())
```

---

---

## HTTP client Sync/Async

You can choose between two clients *httpx (async)* and *requests (sync)*

Async is used by default, if you want to do sync call see example below.

```python
with AppliftingClient(refresh_token="refresh-token", http_backend="requests") as client:
```

---

## 📂 Project Structure

```
applifting_sdk/
├── auth/                  # Token management
├── http/                  # Base HTTP client
├── resources/             # API resources (Products, Offers)
├── models/                # Pydantic request/response models
├── exceptions/          # SDK-specific exceptions
└── config.py               # Environment settings
```

---

## ⚠ Error Handling

The SDK raises clear exceptions for API and network errors:

| Exception             | When it’s raised                            |
| --------------------- |---------------------------------------------|
| `AppliftingSDKError` | Base error for all exceptions               |
| `AuthenticationError` | Invalid or expired refresh/access token     |
| `BadRequestError`     | Invalid request format or parameters        |
| `ValidationFailed`    | 422 validation errors from API              |
| `NotFoundError`       | Resource not found                          |
| `RateLimitError`      | Too many requests (429)                     |
| `ServerError`         | API-side internal error (5xx)               |
| `NetworkError`        | Connection or timeout issues                |

Error handling example:
```python
import asyncio
import os
from dotenv import load_dotenv
from applifting_sdk import AppliftingClient, RegisterProductRequest

from applifting_sdk.exceptions import AppliftingSDKError

load_dotenv()

async def main():
    async with AppliftingClient(refresh_token=os.environ["REFRESH_TOKEN"]) as client:
        try:
            # Register a product
            product = RegisterProductRequest(
                id="5af8e183-ddb1-4e09-9579-4581b2e67b47",
                name="Test Product",
                description="This is a test product."
            )
            registered = await client.products.register_product(product)
            print("Registered:", registered)
        except AppliftingSDKError as e: # This is base error, you can use any other listed above
            print(e)
        

asyncio.run(main())
```
---

## 🛠 Development

Clone and install in editable mode:

```bash
git clone https://github.com/1llyaa/applifting-sdk.git
cd applifting-sdk
pip install -e ".[dev]"
```

Run tests:

```bash
coverage run -m pytest
```


**Author:** Illya Miloserdov
**Version:** 1.0.2

## For reviewers:
Hello reviewers, I hope you'll be happy with my output!! 
Along the way of developing this tool I learned a lot of new things and made huge progress personally.

For the things I haven't known I have had to learn them or use AI (obviously)
I'm willing to learn new things and I think your team will be best match for it.
I want to thank you for this opportunity, and I'm looking forward to see you on another interview and maybe in the 
office as my new colleagues.  

Best regards,
Illya Miloserdov
