# f.a.q. app
#### Video Demo: <https://youtu.be/t60fz9vJjfw>
#### Description:
**f.a.q. app** is my final project for the Harvard's CS50x course.

At its core it's a note-taking app, expanded with robust multi-level category system (which proved to be the biggest challenge, more on that later), as well as a simple user permission level management.

I had two goals going into it: build something useful and learn some new things while doing it.
As far as usefulness goes, idea came from my company. As an IT company, we've got a lot of notes and procedures related to various devices (like cash registers, barcode scanners etc.), which are useful on occasion, but not important enough to memorize them. Some of these notes are scattered in form of 'faq' text files, usually kept with other documents related to particular hardware/software.

I figured a web app we could deploy on our local network would make it easier to keep track of and mantain this knowledge base, not to mention help with onboarding new people in the future.

As far as learning goes, I decided to get more practice with Flask, as well as learn some SQLAlchemy (specifically ORM), which was not covered in CS50x. As it turns out, I also got to learn importance of database design. Originally I hoped to also spend some time learning Tailwind, but eventually decided to skip it for now, write some plain CSS and finish the project earlier.

#### Features:
- Adding, editing, deleting notes
- Filtering notes by category
- Adding, renaming, deleting categories and subcategories
- Registering, editing and deleting users
- User permission management

#### Technologies used:
- Python
  - Flask
  - SQLAlchemy ORM
- HTML
- CSS

#### Usage
During the first run, application will create database file, adding to it default category 'General', as well as a single admin-level user (default username and password can be set in `config.py`), which is needed to assign permissions to newly-registered users. By default, newly registered users are limited to viewing the notes only.

##### Managing users

![Edit user](/readme_img/edit_user.png)

Once a new user is registered, admin user can go into **Manage Users** tab and edit the desired user. In addition to force-changing username and password, admin can choose one of four permission levels:
- Level 1: Read notes only
- Level 2: Read, add notes, edit their own notes
- Level 3: Read, add, edit all notes, manage categories
- Level 4: Admin user

Admin users cannot change their own permissions - they can only be demoted by another admin to avoid situation where there is no admin-level user available.

Users can also be deleted - in this case all the notes they authored must either also be deleted or having their authorship transferred to a default admin user (or another admin-level user, if default admin was removed or demoted). 
Like with permissions - admin user cannot delete himself.

##### Managing categories

![Manage categories](/readme_img/manage_categories.png)

Users of level 3 and above can access **Manage Categories** tab, which lets them do just that - add new categories and rename or delete existing ones.

While adding new category, user has to provide a name, as well as parent category - either 'None' to create a new top-level category, or existing category, to create a subcategory for it. For easier visualisation, list of categories is presented as a tree.

![New category - tree](/readme_img/new_category.png)

Like with users, when we delete a category, we must choose whether to delete all the notes in the category, or to keep them and move them to a parent category. This goes for all of the subcategories as well - all of them are deleted together with a parent category.

##### Notes
Users of level 3 and above can add new notes by selecting **New Note** tab.

![Adding new note](/readme_img/new_note.png)

While title and category are required, text content is optional to allow for quickly adding a bunch of note headers to be expanded on later. There is no WYSIWYG editor for note content, but the whitespace will be preserved.

Users can see 'Edit' link on any note they're permitted to edit or delete. Editing uses similar form, with addition of 'Last updated' timestamp and delete button.

![Editing note](/readme_img/edit_note.png)


#### Files and Directories:
- `faqapp/`
    - `static/` - contains css and static images
    - `templates/` - contains Jinja2 templates
        - `auth/` - login / register templates
        - `category/` - templates for category management
        - `faq/` - templates for index and note editing
        - `users/` - templates for user management
        - `base.html` - base template
    - `__init__.py` - application factory
    - `auth.py` - user authentication, registration and login
    - `extensions.py` - database mapping
    - `faq.py` - main F.A.Q. functionalities - note and category management
    - `models.py` - database object model definitions
    - `users.py` - user management functions
- `config.py` - app configuration file
- `faqapp.db` - database, created on first run

#### Challenges
All the major challenges I encountered in this project can be traced back to my decision of implementing multi-level category structure - it's one thing to hardcode a hierarchy, and whole other thing to allow for everchanging category structure. As it turns out, there are many things to consider to make such a system robust.

To implement it in database, I used a solution loosely based on how it's done in WAPRO ERP software I'm somewhat familiar with.
Each category in the database has two extra columns: tree and level.

**Level** is obviously the level of a category - starting with 0 for top level category.

**Tree** on the other hand is a sequence of numbers (stored as a string) desciribing category's position in a tree, with three digits per level.

For example, tree code for default category General is '000', while the next top-level category would have '001'. Its subcategories would receive '001001', '001002' and so on. This way, we can easily find any subcategory's parent by substring `category.tree[:-3]`.

This structure also makes it easy to build a category list for displaying - we can sort them by tree when requesting from database - this way all subcategories will be right below their respective parent category.

I also needed to include some extra checks for data integrity - for example, when adding a new subcategory, we need to pull all the other subcategories of that parent - so we can assign it a correct tree index.

Likewise, when we're deleting a category, we need to check if it has any subcategories, to avoid orphaned categories.

Of course having three digit tree limits the amount of categories we can add on a given level to 999 - which I consider more than enough, given the scope of this project.

Anoter challenge was ensuring various functions were only available to users with proper permissions. This included permission level check on the front-end, to ensure some elements were not displayed, but also validation on the back-end, to ensure user couldn't get there via rewriting url.

To this end, I had to learn about about wrapper constructors - where appropriate functions are accompanied by a decorator taking required user level as an argument, which then constructs a wrapper around the function:

```
# Decorator for requiring user of specific level
def level_required(level):
    def level_decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if g.user.permission_level < level:
                flash("You don't have permission to access this content.")
                return redirect(url_for("faq.index"))

            return view(**kwargs)

        return wrapped_view
    return level_decorator
```

If the user doesn't meet the requirements, he's returned to index with appropriate error message.

#### TODO / Possible improvements
- Prepare for deployment
- Allow for manually adding new users from management tab
- Allow users to change their own password
- Add configurable subcategory depth limit
- Make subcategories collapsible on index page
- Safety check for trying to add >999th category on a given level

#### Credits and Acknowledgments
- [Flask documentation](https://flask.palletsprojects.com/en/3.0.x/)
- [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/index.html)
- [Flask-SQLAlchemy documentation](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/)
- [WAPRO ERP](https://wapro.pl) for category tree idea.
- [Nord](https://www.nordtheme.com) for UI color scheme.