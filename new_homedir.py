#!/depot/Python-2.7.11_ESSM/bin/python

import paramiko
import lava_params as lp


def ssh_to_server():
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname='us01lava01')
    return ssh_client


def create_homedir(username, uid, gid):
    src_dir_name = lp.src_homedir + ('%s' % username)
    # Connect to ssh server
    ssh_client = ssh_to_server()
    stdin, stdout, stderr = ssh_client.exec_command(
        'ls -ld %s' % src_dir_name)

    output = stdout.read().decode('utf-8').strip()

    if output:
        print('User homedir already exists')
    else:
        # Create a homedir if it does not exist
        stdin, stdout, stderr = ssh_client.exec_command(
            'mkdir %s' % src_dir_name)
        print('Homedirectory created')

        # Change the permissions
        stdin, stdout, stderr = ssh_client.exec_command(
            'chmod 755 %s' % src_dir_name)
        print('755 permissions applied')

        # Change ownership
        stdin, stdout, stderr = ssh_client.exec_command(
            'chown %s:%s %s' % (uid, gid, src_dir_name))
        print('Ownership and default group assigned')

    ssh_client.close()
    print("Connection closed")


def main():
    create_homedir(username, uid, gid)


if __name__ == '__main__':
    main()
