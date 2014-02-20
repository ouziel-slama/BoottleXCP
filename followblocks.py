#! /usr/bin/env python3

from counterpartyd.lib import blocks
from helpers import set_options, init_logging, connect_to_db


if __name__ == '__main__':

    set_options()
    init_logging()
    db = connect_to_db(10000)
    blocks.follow(db)




