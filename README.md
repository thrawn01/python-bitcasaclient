python-bitcasaclient
====================

```
A Command line Interface to the Bitcasa REST API

        PLEASE READ FIRST
            Before you can use the bitcasa client you must follow the
            instructions at https://developer.bitcasa.com/ to create a 'Client
            ID' and 'Client Secret Credentials'

        Now Place your account credentials in ~/.bitcasa
            [bitcasa]
            # This is your app secret
            secret = 79253282352135125cb564243xs2323b
            # This is your client ID
            client-id = 3b73422d
            # This can be anything
            redirect-url = http://example.com
            # Now your login info
            username = username@gmail.com
            password = Y0ur!Passw0rd

        The first time you use the bitcasa client it will use the credentials
        found in ~/.bitcasa to retrieve an API Token which will be used for all
        subsequent API calls. Once retrieved the The API Token will be stored in
        ~/.bitcasa-token

        How the API Works
            The bitcasa API tracks files by the use of a uinque path which
            references a specific revision of a file, so when using bitcasa
            to download or inspect directories you must specify the the path
            to the file or directory, NOT the name of the file or directory.

            For example here is how you download a file from 'My Infinte'

            $ bitcasa ls /
            <BitcasaFolder name=My Infinite, path=/daUzyrTPASqWSFTIp69NyQ>
            $ bitcasa ls /daUzyrTPASqWSFTIp69NyQ
            <BitcasaFile name=IMG_0056.MOV, path=/daUzyrTPQ5qW3JvIp69NyQ/B3kv6mtORPKXSkabpTQupg, size=19076582>
            <BitcasaFile name=IMG_0016.MOV, path=/daUzyrTPQ5qW3JvIp69NyQ/QGX2gsxcvdsDFS3fsdfDFS, size=23423852>
            $ bitcasa get /daUzyrTPQ5qW3JvIp69NyQ/QGX2gsxcvdsDFS3fsdfDFS
            -- Downloading 'IMG_0016.MOV' (/daUzyrTPQ5qW3JvIp69NyQ/QGX2gsxcvdsDFS3fsdfDFS)
            [==========] 100.0%  4114.51 KB/s
            -- 2014-05-05 10:23:13.273717 (1179.44 KB/s) - IMG_0016.MOV saved [23423852/23423852]

        Commands:
            ls [path] [options]         Preforms a directory listing, sends the result the
                                        listing to stdout

            get [path] [options]        Preforms a GET contents on a path, saving the file
                                        contents as the name provided by the api.

            get-dir [path] [options]    Download every file listed in the directory specifed
                                        by the [path] argument

            from-list [file] [options]  Read a list of paths from a file, separated by newlines
                                        download each one of the paths specified

```
