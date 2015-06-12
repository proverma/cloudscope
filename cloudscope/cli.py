# import click
#
# @click.command()
# @click.option('--jenkins-job-url', help='Full url of jenkins job')
#
# def cli(count, name):
#
#
# if __name__ == '__main__':
#     cli()


from xunit import XUnitManager


xu = XUnitManager("intelligence","proverma","cfe5f5f96fcba8979f2f9c30e33d5372","https://glimpse-jenkins.rax.io/job/sage-pull-request/",5288 );
xu.postXunitReports()











