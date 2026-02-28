import typer
from typing import Annotated
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """
    Initialize the database. This will delete all existing data and create a default user "bob".
    """
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User('bob', 'bob@mail.com', 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username: Annotated[str, typer.Argument(help="The username of the user to retrieve")]):
    """
    Get a user by their username.
    """
    # The code for task 5.1 goes here. Once implemented, remove the line below that says "pass"
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """
    Retrieve and print all users in the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(username: Annotated[str, typer.Argument(help="The username of the user whose email is to be changed")], new_email: Annotated[str, typer.Argument(help="The new email address for the user")]):
    """
    Change the email of a given user.
    """
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(
    username: Annotated[str, typer.Argument(help="The username for the new user")],
    email: Annotated[str, typer.Argument(help="The email address for the new user")],
    password: Annotated[str, typer.Argument(help="The password for the new user")]
):
    """
    Create a new user with the specified username, email, and password.
    """
    with get_session() as db: # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command()
def delete_user(
    username: Annotated[str, typer.Argument(help="The username of the user to delete")]
):
    """
    Delete a user by their username.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

@cli.command()
def find_user(
    username: Annotated[str, typer.Argument(help="The username to search for")],
    email: Annotated[str, typer.Argument(help="The email address to search for")]
):
    """
    Find users by username or email (partial matches allowed).
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username.ilike(f'%{username}%') | (User.email.ilike(f'%{email}%')))).all()
        if not user:
            print(f'{username} or {email} not found. User not in database.')
            return
        for u in user:
            print(u)

@cli.command()
def list_n_users(
    limit: Annotated[int, typer.Argument(help="The maximum number of users to list")]=10,
    offset: Annotated[int, typer.Argument(help="The number of users to skip before listing")]=0
):
    """
    List a limited number of users, with optional offset.
    """
    with get_session() as db:
        user = db.exec(select(User).offset(offset).limit(limit)).all()
        if not user:
            print("Offset value to high. Enter lower value.")
            return
        for u in user:
            print(u)

if __name__ == "__main__":
    cli()