#!/depot/Python-2.7.11_ESSM/bin/python

import sys
import ldap
import ldap.modlist as modlist
import argparse
import datetime
import logging

# from lava_params import *
import lava_params as lp
import new_homedir as hd

ldapmodule_trace_level = 0
ldapmodule_trace_file = sys.stdout

# Global variables
currentDT = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connect_to_hq_ldap_server():
    """Setting the connection to LDAP server."""

    # Need this to overcome certificate error
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    # Establish a connection
    l_conn = ldap.initialize('ldap://%s:%s' %
                             (lp.hq_ldap_host, lp.hq_ldap_port),
                             trace_level=ldapmodule_trace_level,
                             trace_file=ldapmodule_trace_file
                             )

    try:
        l_conn.start_tls_s()
        # LDAP bind
        l_conn.simple_bind_s()
        # print('Connection to HQ LDAP server is established')
        return l_conn

    except ldap.LDAPError, error_message:
        print('Error connecting to HQ LDAP server: %s' % error_message)
        return False


def connect_to_sc_ldap_server():
    """Setting the connection to LDAP server."""

    # Need this to overcome certificate error
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    # Establish a connection
    l_conn = ldap.initialize(
        'ldap://%s:%s' % (lp.sc_ldap_host, lp.sc_ldap_port),
        trace_level=ldapmodule_trace_level,
        trace_file=ldapmodule_trace_file
    )

    try:
        l_conn.start_tls_s()
        # LDAP bind
        l_conn.simple_bind_s(lp.ldap_binddn, lp.ldap_bindpw)
        # print('Connection to LDAP server is established')
        return l_conn

    except ldap.LDAPError, error_message:
        print('Error connecting to SC LDAP server: %s' % error_message)
        return False


def ldap_search(l_conn, users_dn, search_filterstr,
                scope=ldap.SCOPE_SUBTREE, attrlist=None):
    """Search LDAP entry. Perform an LDAP search, based on the base dn and an
    attribute filter and returns the result
    """

    try:
        results = l_conn.search_s(users_dn, scope, search_filterstr, attrlist)
        if results:
            user_dn, user_attrs = results[0]
            return user_dn, user_attrs
        else:
            return False

    except ldap.LDAPError, error_message:
        print "Error finding username: %s" % error_message
        return error_message


def ldap_add_user_to_group(l_conn, group_dn, modlist):
    """Add a user to a group"""
    try:
        l_conn.modify_s(group_dn, modlist)
        return True

    except ldap.LDAPError, error_message:
        # print "Error adding a user to a group: %s" % error_message
        return error_message


def ldap_add_user_to_sc(l_conn, dn, modiflist):
    """Add LDAP entry"""
    try:
        l_conn.add_s(dn, modlist.addModlist(modiflist))
        # print 'Userdn: %s added' % dn
        return True

    except ldap.LDAPError, error_message:
        # print "Error adding new user: %s" % error_message
        return error_message


def main():

    print("Inside main function")

    # Create a logging file and update it
    logging.basicConfig(
        filename= lp.log_file,
        level=logging.DEBUG
    )

    # Get username and groupname from the script arguments
    username = sys.argv[1].strip()
    groupname = sys.argv[2].strip()

    print(username, groupname)

    # Make a connection to LDAP server
    l_conn = connect_to_sc_ldap_server()
    hq_l_conn = connect_to_hq_ldap_server()

    # Make a group_dn
    group_dn = 'cn=' + groupname + ',' + lp.sc_groups_dn

    # Check if a user exists in Lava cluster
    if ldap_search(l_conn, lp.sc_users_dn, 'uid=%s' % username):
        logging.info("%s:: User=%s exists in Lava" % (currentDT, username))
        print("%s:: %s exists in Lava" % (currentDT, username))
        sc_user_dn, sc_user_attrs = ldap_search(l_conn, lp.sc_users_dn,
                                                'uid=%s' % username)

        modlist = [(ldap.MOD_ADD, 'member', sc_user_dn)]

        add_user_to_group = ldap_add_user_to_group(l_conn, group_dn, modlist)

        if add_user_to_group == True:
            print('User addition to a group is complete.')
            logging.info("%s:: User=%s addition to group=%s is complete." %
                         (currentDT, username, groupname))
        else:
            logging.warning("%s::%s" % (currentDT, add_user_to_group))

    else:
        logging.info("%s:: User=%s does not exist in Lava. "
                     "Now checking global LDAP" %
                     (currentDT, username))
        # Check if a user exists in global LDAP
        if ldap_search(hq_l_conn, lp.hq_users_dn, 'uid=%s' % username):
            global_user_dn, user_attrs = ldap_search(hq_l_conn, lp.hq_users_dn,
                                                     'uid=%s' % username)

            # Append objectclass to user attributes
            user_attrs['objectClass'] = lp.objectclass

            # Remove unwanted attreibutes
            del user_attrs['mailAlias']
            del user_attrs['mailEnabled']

            # Dynamically fetch uid and gid from global ldap
            uid = user_attrs['uid'][0]
            gid = user_attrs['gidNumber'][0]

            # Make a user_dn string specific to secure cluster
            sc_user_dn = 'uid=' + username + ',' + lp.sc_users_dn

            # Now invoke ldap_add_user function to add a user
            ldap_add_user_to_sc(l_conn, sc_user_dn, user_attrs)

            # Add a new user to a group in secure cluster
            modlist = [(ldap.MOD_ADD, 'member', sc_user_dn)]
            ldap_add_user_to_group(l_conn, group_dn, modlist)
            logging.info('%s:: New user=%s is created and added to group=%s in Lava.' % (
                currentDT, username, groupname))

            # Create a user's homedirectory
            hd.create_homedir(username, uid, gid)

        else:
            # print('User does not exist in Global LDAP as well. Invalid user!')
            logging.warning('%s:: User=%s does not exist in Global LDAP.'
                            ' Invalid user!' % (currentDT, username))


if __name__ == '__main__':
    main()
