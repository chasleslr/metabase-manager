import click
from alive_progress import alive_bar

from metabase_manager.manager import MetabaseManager


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--file",
    "-f",
    default=["metabase.yml"],
    type=click.Path(exists=True),
    multiple=True,
    help="Path(s) to YAML configuration file.",
)
@click.option(
    "--host",
    "-h",
    envvar="METABASE_HOST",
    required=True,
    help="Metabase URL (ex. https://<org>.metabaseapp.com)",
)
@click.option(
    "--user", "-u", envvar="METABASE_USER", required=True, help="Metabase user"
)
@click.option(
    "--password",
    "-p",
    envvar="METABASE_PASSWORD",
    required=True,
    help="Metabase password",
)
@click.option(
    "--select",
    "-s",
    type=click.Choice(MetabaseManager.get_allowed_keys()),
    multiple=True,
    help="Sync only certain objects.",
)
@click.option(
    "--exclude",
    "-e",
    type=click.Choice(MetabaseManager.get_allowed_keys()),
    multiple=True,
    help="Don't sync certain objects.",
)
@click.option(
    "--no-delete",
    is_flag=True,
    help="Don't run the delete step (only create/update existing objects).",
)
@click.option("--silent", is_flag=True, help="Don't print logs.")
@click.option(
    "--dry-run", is_flag=True, help="Don't execute commands that mutate Metabase."
)
def sync(file, host, user, password, select, exclude, no_delete, silent, dry_run):
    """
    Sync your declared configuration to Metabase.
    """
    manager = MetabaseManager(
        select=select,
        exclude=exclude,
        metabase_host=host,
        metabase_user=user,
        metabase_password=password,
    )
    manager.parse_config(paths=file)
    manager.cache_metabase()

    with alive_bar(
        total=len(manager.get_entities_to_manage()),
        bar=None,
        spinner="dots",
        stats=False,
        stats_end=False,
        enrich_print=False,
        receipt=True,
        elapsed="[{elapsed}]",
        disable=silent,
    ) as bar:
        for obj in manager.get_entities_to_manage():
            bar.text(obj.__name__)
            manager.cache_metabase()

            for entity in manager.find_objects_to_create(obj):
                if not silent:
                    click.echo(click.style(f"[CREATE] {entity}", fg="green"))
                if not dry_run:
                    manager.create(entity)

            for entity in manager.find_objects_to_update(obj):
                if not silent:
                    click.echo(click.style(f"[UPDATE] {entity}", fg="yellow"))
                if not dry_run:
                    manager.update(entity)

            if not no_delete:
                for entity in manager.find_objects_to_delete(obj):
                    if not silent:
                        click.echo(click.style(f"[DELETE] {entity}", fg="red"))
                    if not dry_run:
                        manager.delete(entity)

            bar()
