from fastapi import FastAPI

import database
import routes

app = FastAPI(lifespan=database.database_setup)

app.include_router(routes.auth_router)
app.include_router(routes.users_router)
app.include_router(routes.wallet_router)
app.include_router(routes.transaction_router)
