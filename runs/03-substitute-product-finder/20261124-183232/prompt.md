Build a simple Python FastAPI app using Beanie ODM and Azure DocumentDB to store product JSON documents. Generate embeddings for product attributes, store the vectors in the database, and expose a /substitute endpoint that accepts a product ID and returns the 5 closest alternatives by cosine similarity using Azure DocumentDB vector search.

The app should include a script to ingest 10,000 product transactions. The app should include an artistic UI to look like an online retailer's website.

Use a config file for the Azure DocumentDB connection string and display a clear error if the connection string is missing or invalid. Keep the code as simple and readable as possible.

Can you add detailed comments before each method to make code readability by others as easy as possible?
