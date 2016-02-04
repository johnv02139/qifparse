# -*- coding: utf-8 -*-
import six
from datetime import datetime
from decimal import Decimal
from qifparse.qif import (
    Transaction,
    MemorizedTransaction,
    AmountSplit,
    Account,
    Investment,
    Category,
    Class,
    Tag,
    Qif,
    DEFAULT_ACCOUNT_TYPE,
)

TYPE_HEADER = '!Type:'

NON_INVST_ACCOUNT_TYPES = [
    TYPE_HEADER + DEFAULT_ACCOUNT_TYPE,
    TYPE_HEADER + 'Bank',
    TYPE_HEADER + 'Ccard',
    TYPE_HEADER + 'Oth A',
    TYPE_HEADER + 'Oth L',
    TYPE_HEADER + 'Invoice',  # Quicken for business only
    TYPE_HEADER + 'CCard',    # Preferred capitalization
]

def is_obfuscated_account_type (account_type):
    """Recognize a type that is not written with a documented name.

    Don't know what causes Quicken to generate these lines.  It certainly
    appears undocumented, to say the least, but Quicken 2008 for Windows
    seems to emit them often.

    Not sure if this code is good, canonical Python or not.  It says:
    if the following are true:
    - the characters in the type name contain at least two irregular
      characters
      - where, "irregular" means, outside the ASCII range from '!'
        through 'z'
      - in practice, the characters are control characters (<= 26) or
        tilde
    then, we assume this is an "obfuscated" type.

    Again, the idea that it's "obfuscated" is a guess, that Intuit
    decided to hide the type for some reason.  Maybe it's just a bug.

    We don't know what this means, but it seems to only happen in non-
    investment transaction types, and we will just translate this into
    "Cash".  Note, this will fail a regression test of the type used in
    the test_parse test, because when re-writing a type like this, it
    will be written as "Cash", and not as the strange sequence of
    characters that was input.

    """
    return 2 <= len([x for x in account_type if not (33 <= ord(x) <= 125)])

def is_obfuscated_type_header (first_line):
    """Recognize a type header that is not written with a documented name.

    That means, check that it begins with TYPE_HEADER, and then what follows
    satisfies the "is_obfuscated_account_type" check
    """
    return first_line.startswith(TYPE_HEADER) and \
        is_obfuscated_account_type(first_line[len(TYPE_HEADER):])

class QifParserException(Exception):
    pass


class QifParser(object):

    date_format = None

    @classmethod
    def parse(cls_, file_handle, date_format=None):
        if isinstance(file_handle, type('')):
            raise RuntimeError(
                six.u("parse() takes in a file handle, not a string"))
        data = file_handle.read()
        if len(data) == 0:
            raise QifParserException('Data is empty')
        cls_.date_format = date_format
        cls_.auto_switches = 0
        cls_.qif_obj = Qif()
        cls_.parseData(data)
        return cls_.qif_obj

    @classmethod
    def parseData(cls_, data):
        chunks = data.split('\n^\n')
        last_type = None
        last_account = None
        transactions_header = None
        for chunk in chunks:
            if chunk:
                (last_type, transactions_header, last_account) \
                    = cls_.parseChunk(chunk, last_type,
                                      transactions_header, last_account)

    @classmethod
    def parseChunk(cls_, chunk, last_type, transactions_header, last_account):
        parsers = {
            'category': cls_.parseCategory,
            'account': cls_.parseAccount,
            'transaction': cls_.parseTransaction,
            'investment': cls_.parseInvestment,
            'class': cls_.parseClass,
            'tag': cls_.parseTag,
            'memorized': cls_.parseMemorizedTransaction
        }

        (next_type, new_header) = cls_.parseType(chunk)
        if next_type:
            last_type = next_type
        if new_header:
            transactions_header = new_header

        # if no header is found, we use the previous one
        item = parsers[last_type](chunk)
        if last_type == 'account':
            cls_.qif_obj.add_account(item)
            last_account = item
        elif last_type == 'memorized':
            last_account = None
            cls_.qif_obj.add_transaction(item, header=transactions_header)
        elif last_type == 'transaction' or last_type == 'investment':
            if last_account:
                last_account.add_transaction(item, header=transactions_header)
            else:
                cls_.qif_obj.add_transaction(item, header=transactions_header)
        elif last_type == 'category':
            cls_.qif_obj.add_category(item)
        elif last_type == 'class':
            cls_.qif_obj.add_class(item)
        elif last_type == 'tag':
            cls_.qif_obj.add_tag(item)
        return (last_type, transactions_header, last_account)

    @classmethod
    def parseType(cls_, chunk):
        lines = chunk.splitlines()

        index = 0
        first_line = lines[index].strip()
        while first_line == '!Clear:AutoSwitch' or \
              first_line == '!Option:AutoSwitch':
            index += 1
            cls_.auto_switches += 1
            first_line = lines[index].strip()

        if first_line == '!Account':
            return ('account', None)
        elif first_line == TYPE_HEADER + 'Cat':
            return ('category', None)
        elif first_line in NON_INVST_ACCOUNT_TYPES:
            return ('transaction', first_line)
        elif first_line == TYPE_HEADER + 'Invst':
            return ('investment', first_line)
        elif first_line == TYPE_HEADER + 'Class':
            return ('class', None)
        elif first_line == TYPE_HEADER + 'Memorized':
            return ('memorized', first_line)
        elif is_obfuscated_type_header(first_line):
            return ('transaction', TYPE_HEADER + DEFAULT_ACCOUNT_TYPE)
        elif first_line == TYPE_HEADER + 'Tag':
            return ('tag', None)
        elif first_line.startswith('!'):
            raise QifParserException('Section header not recognized: ' +
                                     first_line)
        else:
            return (None, None)

    @classmethod
    def parseClass(cls_, chunk):
        """
        """
        curItem = Class()
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or \
                    line.startswith(TYPE_HEADER + 'Class'):
                continue
            elif line[0] == 'N':
                curItem.name = line[1:]
            elif line[0] == 'D':
                curItem.description = line[1:]
        return curItem

    @classmethod
    def parseTag(cls_, chunk):
        """
        """
        curItem = Tag()
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or \
                    line.startswith(TYPE_HEADER + 'Tag'):
                continue
            elif line[0] == 'N':
                curItem.name = line[1:]
            elif line[0] == 'D':
                curItem.description = line[1:]
        return curItem

    @classmethod
    def parseCategory(cls_, chunk):
        """
        """
        curItem = Category()
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or line.startswith(TYPE_HEADER):
                continue
            elif line[0] == 'E':
                curItem.expense_category = True
            elif line[0] == 'I':
                curItem.income_category = True
                curItem.expense_category = False  # if ommitted is True
            elif line[0] == 'T':
                curItem.tax_related = True
            elif line[0] == 'D':
                curItem.description = line[1:]
            elif line[0] == 'B':
                curItem.budget_amount = line[1:]
            elif line[0] == 'R':
                curItem.tax_schedule_info = line[1:]
            elif line[0] == 'N':
                curItem.name = line[1:]
        return curItem

    @classmethod
    def parseAccount(cls_, chunk):
        """
        """
        curItem = Account()
        curItem.is_auto_switch = (cls_.auto_switches == 1)
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or line.startswith('!Account'):
                continue
            elif line[0] == 'N':
                curItem.name = line[1:]
            elif line[0] == 'D':
                curItem.description = line[1:]
            elif line[0] == 'T':
                account_type = line[1:]
                if is_obfuscated_account_type(account_type):
                    curItem.account_type = DEFAULT_ACCOUNT_TYPE
                else:
                    curItem.account_type = account_type
            elif line[0] == 'L':
                curItem.credit_limit = line[1:]
            elif line[0] == '/':
                curItem.balance_date = cls_.parseQifDateTime(line[1:])
            elif line[0] == '$':
                curItem.balance_amount = line[1:]
            elif line == '!Clear:AutoSwitch' or line == '!Option:AutoSwitch':
                pass
            else:
                print('Line of account not recognized: ' + line)
        return curItem

    @classmethod
    def parseMemorizedTransaction(cls_, chunk):
        """
        """

        curItem = MemorizedTransaction()
        if cls_.date_format:
            curItem.date_format = cls_.date_format
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or \
                    line.startswith(TYPE_HEADER + 'Memorized'):
                continue
            elif line[0] == 'T':
                curItem.amount = cls_.parseFloat(line[1:])
            elif line[0] == 'U':
                curItem.uamount = cls_.parseFloat(line[1:])
            elif line[0] == 'C':
                curItem.cleared = line[1:]
            elif line[0] == 'P':
                curItem.payee = line[1:]
            elif line[0] == 'M':
                curItem.memo = line[1:]
            elif line[0] == 'K':
                curItem.mtype = line[1:]
            elif line[0] == 'A':
                if not curItem.address:
                    curItem.address = []
                curItem.address.append(line[1:])
            elif line[0] == 'L':
                cat = line[1:]
                if cat.startswith('['):
                    curItem.to_account = cat[1:-1]
                else:
                    curItem.category = cat
            elif line[0] == 'S':
                curItem.splits.append(AmountSplit())
                split = curItem.splits[-1]
                cat = line[1:]
                if cat.startswith('['):
                    split.to_account = cat[1:-1]
                else:
                    split.category = cat
            elif line[0] == 'E':
                split = curItem.splits[-1]
                split.memo = line[1:-1]
            elif line[0] == 'A':
                split = curItem.splits[-1]
                if not split.address:
                    split.address = []
                split.address.append(line[1:])
            elif line[0] == '$':
                amt = cls_.parseFloat(line[1:-1])
                if amt:
                    if curItem.splits:
                        split = curItem.splits[-1]
                        split.amount = amt
                    else:
                        raise QifParserException('no split found')
            else:
                # don't recognize this line; ignore it
                print ("Skipping unknown line of memorized transaction:\n" +
                       str(line))
        return curItem

    @classmethod
    def parseTransaction(cls_, chunk):
        """
        """

        curItem = Transaction()
        if cls_.date_format:
            curItem.date_format = cls_.date_format
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or line.startswith(TYPE_HEADER):
                continue
            elif line[0] == 'D':
                curItem.date = cls_.parseQifDateTime(line[1:])
            elif line[0] == 'N':
                curItem.num = line[1:]
            elif line[0] == 'T':
                curItem.amount = cls_.parseFloat(line[1:])
            elif line[0] == 'U':
                curItem.uamount = cls_.parseFloat(line[1:])
            elif line[0] == 'C':
                curItem.cleared = line[1:]
            elif line[0] == 'P':
                curItem.payee = line[1:]
            elif line[0] == 'M':
                curItem.memo = line[1:]
            elif line[0] == '1':
                curItem.first_payment_date = line[1:]
            elif line[0] == '2':
                curItem.years_of_loan = line[1:]
            elif line[0] == '3':
                curItem.num_payments_done = line[1:]
            elif line[0] == '4':
                curItem.periods_per_year = line[1:]
            elif line[0] == '5':
                curItem.interests_rate = line[1:]
            elif line[0] == '6':
                curItem.current_loan_balance = line[1:]
            elif line[0] == '7':
                curItem.original_loan_amount = line[1:]
            elif line[0] == 'A':
                if not curItem.address:
                    curItem.address = []
                curItem.address.append(line[1:])
            elif line[0] == 'L':
                cat = line[1:]
                if cat.startswith('['):
                    curItem.to_account = cat[1:-1]
                else:
                    curItem.category = cat
            elif line[0] == 'S':
                curItem.splits.append(AmountSplit())
                split = curItem.splits[-1]
                cat = line[1:]
                if cat.startswith('['):
                    split.to_account = cat[1:-1]
                else:
                    split.category = cat
            elif line[0] == 'E':
                split = curItem.splits[-1]
                split.memo = line[1:-1]
            elif line[0] == 'A':
                split = curItem.splits[-1]
                if not split.address:
                    split.address = []
                split.address.append(line[1:])
            elif line[0] == '$':
                split = curItem.splits[-1]
                split.amount = cls_.parseFloat(line[1:-1])
            else:
                # don't recognize this line; ignore it
                print ("Skipping unknown line of transaction:\n" + str(line))
        return curItem

    @classmethod
    def parseInvestment(cls_, chunk):
        """
        """

        curItem = Investment()
        if cls_.date_format:
            curItem.date_format = cls_.date_format
        lines = chunk.splitlines()
        for line in lines:
            if not len(line) or line[0] == '\n' or line.startswith(TYPE_HEADER):
                continue
            elif line[0] == 'D':
                curItem.date = cls_.parseQifDateTime(line[1:])
            elif line[0] == 'T':
                curItem.amount = cls_.parseFloat(line[1:])
            elif line[0] == 'N':
                curItem.action = line[1:]
            elif line[0] == 'Y':
                curItem.security = line[1:]
            elif line[0] == 'I':
                curItem.price = cls_.parseFloat(line[1:])
            elif line[0] == 'Q':
                curItem.quantity = cls_.parseFloat(line[1:])
            elif line[0] == 'C':
                curItem.cleared = line[1:]
            elif line[0] == 'M':
                curItem.memo = line[1:]
            elif line[0] == 'P':
                curItem.first_line = line[1:]
            elif line[0] == 'L':
                curItem.to_account = line[2:-1]
            elif line[0] == '$':
                curItem.amount_transfer = cls_.parseFloat(line[1:])
            elif line[0] == 'O':
                curItem.commission = cls_.parseFloat(line[1:])
        return curItem

    @classmethod
    def parseFloat(cls_, chunk):
        """convert from QIF float format to a quantity

        To avoid rounding errors, use a Decimal class rather than float.
        Sometimes the QIF file will contain an amount that is formatted
        with a separator, e.g., "1,234.00".  Removing commas is a quick-
        and-dirty way to parse such strings.

        Note that many countries in the world use a decimal comma and a
        dot separator, e.g., "1.234,00".  I don't know what Quicken does
        with the separator, but it does seem to standardize on the dot
        even in locales that normally use a comma, so it's possible this
        might work.

        I'd need help testing this using QIF files from other locales.
        I don't have access to any.
        """
        return Decimal(chunk.replace(',', ''))

    @classmethod
    def parseQifDateTime(cls_, qdate):
        """ convert from QIF time format to ISO date string

        QIF is like "7/ 9/98"  "9/ 7/99" or "10/10/99" or "10/10'01" for y2k
             or, it seems (citibankdownload 20002) like "01/22/2002"
             or, (Paypal 2011) like "3/2/2011".
        ISO is like   YYYY-MM-DD  I think @@check
        """

        if cls_.date_format:
            if "'" in qdate:
                # It's probably necessary that we'll need to modify the
                # string in some cases, though this particular change is
                # quick and dirty.  TODO: need to revisit.
                nice_date = qdate.replace("' ", "/0")
                nice_date = nice_date.replace("'", "/")
            else:
                nice_date = qdate
            return datetime.strptime(nice_date, cls_.date_format)

        # If date_format is not given explicitly, we will try to guess...
        if qdate[1] == "/":
            qdate = "0" + qdate   # Extend month to 2 digits
        if qdate[4] == "/":
            qdate = qdate[:3]+"0" + qdate[3:]  # Extend month to 2 digits
        for i in range(len(qdate)):
            if qdate[i] == " ":
                qdate = qdate[:i] + "0" + qdate[i+1:]
        if len(qdate) == 10:  # new form with YYYY date
            iso_date = qdate[6:10] + "-" + qdate[3:5] + "-" + qdate[0:2]
            return datetime.strptime(iso_date, '%Y-%m-%d')
        if qdate[5] == "'":
            C = "20"
        else:
            C = "19"
        iso_date = C + qdate[6:8] + "-" + qdate[3:5] + "-" + qdate[0:2]
        return datetime.strptime(iso_date, '%Y-%m-%d')
