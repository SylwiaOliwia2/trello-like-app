# Task manager

## general purpose

I need an app, which I'll use as an app for QA testing (E2E, API, integration tests). FYI his QA test suite will be my recruitment portfolio. The app doesn't need be well designed (when it comes to code architecture), better simple, but working, rather than overengineering.
As for now, I want you to create only an app.

## Business logic

### Usability

The app allows to manage tasks (in a Trello-like way):

- The user can create board
- On the board, the users can create lists.
- Inside the list, user can create a task.
- users can manage the tasks: move them between the lists, delete, edit
- users can add the following tags to the task: ("Important", "Needs Definition", "Unscoped")
- Each task may have assigned member (single member)
- User may add a due date to the task (both date and time). This feature has lowest priority.
- Task must have title, description and comments.
- user may edit his profile by changing his username and password (optionally other issues if they are easy to implement)
- user needs to login to have access to the app (as a later stage of development, user must use MFA)
- Trello has workspaces. Ignore them in this project.

### User permissions

The app may have multiple users. You can assume the same way of permission management, as in Trello (who owns the board and is allowed to add users to the board). If it's complicated, you can simplify it. Once you create the app, describe the user permissions in README.md
