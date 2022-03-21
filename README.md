# metabase-manager

Manage your Metabase instance programmatically by declaring your desired state. Metabase-manager will create, update,
and delete objects in Metabase to ensure to it matches your declared configuration.


## Installation

```shell
pip install metabase-manager
```


## Usage

Here is an example configuration for Users and Groups:
```yaml
# metabase.yaml

users:
  - email: jdoe@example.com
    first_name: Jane
    last_name: Doe
    groups:
      - Admin
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
metabase-manager sync --host=https://<org>.metabaseapp.com --user <email> --password <password>
```


### Supported Entities
- Users
- Groups
