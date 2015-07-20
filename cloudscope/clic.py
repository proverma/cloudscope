import click
from xunit import XUnitManager


@click.command()
@click.option('--project',
              help="enter the product name; for example: product=intelligence")
@click.option('--user', help="enter your user name")
@click.option('--password',
              help="enter the api key which will be something,like this:" +
              "cfe5f5f96fcba8979f2f9c30e33d5372")
@click.option('--job_url',
              help="enter the jenkin url where all the jobs are kept")
@click.option('--last_build_number',
              help="enter the build number from where you want the details")
def call_xunit_manager(project, user, password, job_url, last_build_number):
    xu = XUnitManager(project, user, password, job_url, last_build_number)
    xu.post_xunit_reports()


if __name__ == '__main__':
    call_xunit_manager()
