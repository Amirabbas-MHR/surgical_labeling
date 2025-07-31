📄 ROUTES.md – Application Routes
/

    Method: GET / POST

    Use: Login page for all users (including admin).

    POST fields:

        username

        password

    Redirects to:

        /label/<username>/0 if expert logs in

        /admin if admin logs in (manual step in admin route)

/label/<username>/<int:idx>

    Method: GET / POST

    Use: Expert labeling interface.

    Functionality:

        Shows the current image to be labeled by expert username.

        If image already labeled, skips to the next.

        On POST, saves the label to SQLite and redirects to next image.

    Progress Displayed: e.g. "Progress: 152/800 images labeled"

/admin

    Method: GET / POST

    Use: Admin login and data table display.

    POST fields:

        username (must be "admin")

        password

    Renders: a pivoted HTML table of all labels (image x expert)

/admin/download

    Method: GET

    Use: Downloads the current labeled dataset as backup.csv

    File format: CSV with 800 rows and one column per expert

💾 Data Storage

    Database: SQLite (results/labels.db)

    Backup CSV: Automatically written to results/backup.csv after every label.
