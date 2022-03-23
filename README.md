# metabase-manager

Manage your Metabase instance programmatically by declaring your desired state. `metabase-manager` will create, update,
and delete objects in Metabase to ensure to it matches your declared configuration.


## Installation

```shell
pip install metabase-manager
```


## Usage

Here is an example configuration for Users and Groups:
```yaml
# metabase.yml

users:
  - email: jdoe@example.com
    first_name: Jane
    last_name: Doe
    groups:
      - Administrators
      - Finance

  - name: jsmith@example.com
    first_name: John
    last_name: Smith
    groups:
      - Marketing

groups:
  - name: Finance
  - name: Marketing
```

By running the following command, `metabase-manager` will create these users and groups if they don't already exist,
update them if some attributes differ, and delete users and groups that exist in Metabase but are not declared here.
```shell
metabase-manager sync
```

```shell
[CREATE] Group(name='Finance')
[CREATE] Group(name='Marketing')
[DELETE] Group(name='Sales')      # Sales is not defined in metabase.yml
[CREATE] User(first_name='Jane', last_name='Doe', email='jdoe@example.com', groups=[Group(name='Administrators'), Group(name='Finance')])
# jsmith@example.com already exists in Metabase, but some attributes or group membership differ
[UPDATE] User(first_name='John', last_name='Smith', email='jsmith@example.com', groups=[Group(name='Marketing')])
```

### Credentials

It is possible to provide credentials to your Metabase instance through the command-line as follows:

```shell
metabase-manager sync --host=https://<org>.metabaseapp.com --user <email> --password <password>
```

It is also possible to provide credentials as environment variables. `metabase-manager` will automatically use
these variables if they are set in the environment.

- `METABASE_HOST=<host>`
- `METABASE_USER=<user>`
- `METABASE_PASSWORD=<password>`


### Configuration

By default, `metabase-manager` will expect to find a `metabase.yml` file in the current directory. You can override this
default, and optionally provide more than one file, with the `--file/-f` parameter.

```shell
metabase-manager sync -f users.yml -f <directory>/groups.yml
```

### Selection

It is possible to run your sync only for certain types of objects by using the `--select/-s` or `--exclude/-e` options.

```shell
metabase-manager sync --select users  # only users will be synced
```

```shell
metabase-manager sync --exclude users  # everything by users will be synced
```


### Dry Run

It is possible to execute a dry run to see which objects would be created, updated, or deleted given your configuration.
This will only log the changes, but not actually execute any changes on your Metabase instance.

```shell
metabase-manager sync --dry-run
```


### Upsert Only

If you do not want `metabase-manager` to delete anything in your Metabase instance, you can use the `--no-delete` flag.
This is useful if your `metabase.yml` configuration file does not exhaustively define object that you wish to exist in
your Metabase instance.

```shell
metabase-manager sync --no-delete
```



### Supported Entities

Currently, it is possible to manage the following entities:

- Users
- Groups
