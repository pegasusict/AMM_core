"""Base file for AMM core functionality."""
from fastapi import FastAPI

from .Singletons.Stack import Stack
from graphql import GraphQL

def main():
    """Main function to run the AMM core functionality."""
    stack = Stack()



    fastapi = FastAPI()
    graphql = GraphQL(fastapi)
    graphql.add_graphql_route("/")
    graphql.run()

if __name__ == "__main__":
    main()
