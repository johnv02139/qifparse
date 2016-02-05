# -*- coding: utf-8 -*-
import unittest
import os
from datetime import datetime
from decimal import Decimal
from qifparse.parser import QifParser

filename = os.path.join(os.path.dirname(__file__), 'win2008.qif')
date_format = '%m/%d/%y'

def get_account(qif_obj, name):
    accts = qif_obj.get_accounts(name)
    if not accts:
        raise Exception('no account found with name %s' % name)
    elif len(accts) > 1:
        raise Exception('too many accounts found with name %s: %d' % (name, len(accts)))
    else:
        return accts[0]

class TestQIFParsing(unittest.TestCase):

    def testReadQuickenWin2008File(self):
        qif = QifParser.parseFile(filename, date_format)

        self.assertFalse(qif.get_classes())

        categories = qif.get_categories()

        # The Quicken file from which the test QIF is exported defines several
        # categories, including 'Auto' and 'Tax'; each of those two have
        # specific, defined subcategories.  All told, the number of leaves of
        # the category tree in the file is 13.  The QIF contains 15, though; for
        # the top-level categories which have subcategories, it defines one
        # category plainly ('Tax'), but also defines a subcategory: 'Tax:ZZZZZ'.
        # This seems vaguely wrong to me, and we may want to have the parser
        # exclude the ZZZZZ subcategories.
        fake_subcat = 'ZZZZZ'
        defined = [x for x in categories if not x.name.endswith(':' + fake_subcat)]
        fake = [x for x in categories if x.name.endswith(':' + fake_subcat)]
        self.assertEqual(len(defined), 13)
        self.assertEqual(len(fake), 2)

        alpha_cats = sorted(defined, key=lambda x: x.name)

        self.assertEqual(alpha_cats[0].name, 'Auto')
        self.assertEqual(alpha_cats[0].description, 'Automobile Expenses')
        self.assertTrue(alpha_cats[0].expense_category)

        self.assertEqual(alpha_cats[1].name, 'Auto:Gas')
        self.assertEqual(alpha_cats[1].description, 'Gas, Diesel')
        self.assertTrue(alpha_cats[1].expense_category)

        self.assertEqual(alpha_cats[2].name, 'Auto:Registration (Non-taxable)')
        self.assertEqual(alpha_cats[2].description, 'Auto Registration')
        self.assertTrue(alpha_cats[2].expense_category)

        self.assertEqual(alpha_cats[3].name, 'Auto:Registration (Taxable)')
        self.assertEqual(alpha_cats[3].description, 'Auto Registration')
        self.assertTrue(alpha_cats[3].expense_category)

        self.assertEqual(alpha_cats[4].name, 'Dining')
        self.assertEqual(alpha_cats[4].description, 'Dining Out')
        self.assertTrue(alpha_cats[4].expense_category)

        self.assertEqual(alpha_cats[5].name, 'Groceries')
        self.assertEqual(alpha_cats[5].description, 'Groceries')
        self.assertTrue(alpha_cats[5].expense_category)

        self.assertEqual(alpha_cats[6].name, 'Medical')
        self.assertEqual(alpha_cats[6].description, 'Medical Expense')
        self.assertTrue(alpha_cats[6].expense_category)
        self.assertTrue(alpha_cats[6].tax_related)
        self.assertEqual(alpha_cats[6].tax_schedule_info, '4368')

        self.assertEqual(alpha_cats[7].name, 'Salary')
        self.assertEqual(alpha_cats[7].description, 'Salary Income')
        self.assertFalse(alpha_cats[7].expense_category)
        self.assertTrue(alpha_cats[7].income_category)
        self.assertTrue(alpha_cats[7].tax_related)
        self.assertEqual(alpha_cats[7].tax_schedule_info, '7360')

        self.assertEqual(alpha_cats[8].name, 'Tax')
        self.assertEqual(alpha_cats[8].description, 'Taxes')
        self.assertTrue(alpha_cats[8].expense_category)
        self.assertTrue(alpha_cats[8].tax_related)

        self.assertEqual(alpha_cats[9].name, 'Tax:Fed')
        self.assertEqual(alpha_cats[9].description, 'Federal Tax')
        self.assertTrue(alpha_cats[9].expense_category)
        self.assertTrue(alpha_cats[9].tax_related)
        self.assertEqual(alpha_cats[9].tax_schedule_info, '7376')

        self.assertEqual(alpha_cats[10].name, 'Tax:Medicare')
        self.assertEqual(alpha_cats[10].description, 'Medicare Tax')
        self.assertTrue(alpha_cats[10].expense_category)
        self.assertTrue(alpha_cats[10].tax_related)
        self.assertEqual(alpha_cats[10].tax_schedule_info, '7680')

        self.assertEqual(alpha_cats[11].name, 'Tax:Soc Sec')
        self.assertEqual(alpha_cats[11].description, 'Soc Sec Tax')
        self.assertTrue(alpha_cats[11].expense_category)
        self.assertTrue(alpha_cats[11].tax_related)
        self.assertEqual(alpha_cats[11].tax_schedule_info, '7392')

        self.assertEqual(alpha_cats[12].name, 'Tax:State')
        self.assertEqual(alpha_cats[12].description, 'State Tax')
        self.assertTrue(alpha_cats[12].expense_category)
        self.assertTrue(alpha_cats[12].tax_related)
        self.assertEqual(alpha_cats[12].tax_schedule_info, '7424')

        self.assertEqual(1, len(qif.get_tags()))
        tag = qif.get_tags()[0]
        self.assertEqual('Sandwiches', tag.name)
        self.assertEqual('Meals eaten between bread', tag.description)

        accounts = qif.get_accounts()
        categories = qif.get_categories()

        cc = get_account(qif, 'Credit Card')
        bank = get_account(qif, 'My Bank')
        car = get_account(qif, 'Fancy Car')

        self.assertEqual(cc.name, 'Credit Card')
        self.assertEqual(cc._type, 'CCard')
        self.assertEqual(cc.credit_limit, '1,000,000.00')
        self.assertFalse(cc._transactions)

        self.assertEqual(bank.name, 'My Bank')
        self.assertEqual(bank._type, 'Bank')
        self.assertEqual(bank.description, 'Personal Checking Account')
        trns = bank._transactions
        # It appears the transactions are parsed into a dictionary, where the
        # keys are the header lines.  One thing this does (and which might be
        # the reason for the choice) is to separate "memorized transactions"
        # from other ones.  Theoretically, it also separates 'Bank' transactions
        # from 'Cash', from 'CCard', etc.  But can those different types of
        # transactions be associated with a single account?  Or is it just, for
        # a 'Bank' account, we have 'Bank' transactions and memorized
        # transactions?  For a 'CCard' account, we have 'CCard' and memorized?
        # That's what I'm assuming.  I still may look to change the actual keys
        # that are used for the dictionary, in the future.  For now, expect the
        # current behavior.
        self.assertTrue('!Type:Bank' in trns.keys())
        bank_trans = trns['!Type:Bank']

        self.assertEqual(len(bank_trans), 3)

        b1 = bank_trans[0]
        b2 = bank_trans[1]
        b3 = bank_trans[2]

        self.assertEqual(b1.amount, Decimal('100000.00'))
        # The 'U' data is undocumented, and seems to always agree exactly with
        # the 'T' data.  Expect that to be the case.
        self.assertEqual(b1.uamount, b1.amount)
        self.assertEqual(b1.cleared, 'X')
        # Note, in the QIF file, the date is written as 'D3/31/1999', with no
        # leading zero before the month.
        self.assertEqual(b1.date, datetime(1999, 3, 31, 0, 0))
        self.assertEqual(b1.memo, 'This may be written to the QIF with a comma')
        self.assertEqual(b1.num, None)
        self.assertEqual(b1.payee, 'Opening Balance')
        self.assertEqual(b1.splits, [])
        self.assertEqual(b1.to_account, 'My Bank')

        self.assertEqual(b2.address, None)
        self.assertEqual(b2.amount, Decimal('-20000.00'))
        self.assertEqual(b2.uamount, b2.amount)
        self.assertEqual(b2.category, 'Auto')
        self.assertEqual(b2.cleared, '*')
        self.assertEqual(b2.date, datetime(2002, 12, 31, 0, 0))
        self.assertEqual(b2.memo, None)
        self.assertEqual(b2.num, '104')
        self.assertEqual(b2.payee, 'Fancy Car Dealer')
        self.assertEqual(b2.splits, [])
        self.assertEqual(b2.to_account, None)

        self.assertEqual(b3.address, None)
        self.assertEqual(b3.amount, Decimal('-45.00'))
        self.assertEqual(b3.uamount, b3.amount)
        self.assertEqual(b3.category, 'Auto:Gas')
        self.assertEqual(b3.cleared, None)
        self.assertEqual(b3.date, datetime(2003, 1, 15, 0, 0))
        self.assertEqual(b3.memo, None)
        self.assertEqual(b3.num, None)
        self.assertEqual(b3.payee, 'Sunoco')
        self.assertEqual(b3.splits, [])
        self.assertEqual(b3.to_account, None)

        self.assertEqual(car.name, 'Fancy Car')
        self.assertEqual(car._type, 'Oth A')
        trns = car._transactions
        self.assertTrue('!Type:Oth A' in trns.keys())
        car_trans = trns['!Type:Oth A']

        c1 = car_trans[0]

        self.assertEqual(c1.category, None)
        self.assertEqual(c1.to_account, 'Fancy Car')
        self.assertEqual(c1.memo, None)
        self.assertEqual(c1.payee, 'Opening Balance')
        self.assertEqual(c1.amount, Decimal('20000.00'))
        self.assertEqual(c1.num, None)
        self.assertEqual(c1.address, None)
        self.assertEqual(c1.date, datetime(2002, 12, 31, 0, 0))
        self.assertEqual(c1.cleared, None)
        self.assertEqual(c1.uamount, Decimal('20000.00'))
        self.assertEqual(c1.splits, [])

        # Actual transactions should be associated with accounts.  The parser will
        # also potentially allow "top-level" transactions which are just associated
        # with the QIF object, but this should not happen.
        #
        # However, "memorized transactions", which are really not transactions at
        # all, do get attached at the top level.

        detached_trans = qif.get_transactions()
        # Should assert that this list has exactly one element (a list)
        # Should assert that all the transactions in this list are of type memorized
        memorized = detached_trans[0]

        # KC        Check transaction
        # KI        Investment transaction
        # KE        Electronic payee transaction

        # KP        Payment transaction
        self.assertEqual(memorized[0]._mtype, 'P')
        self.assertEqual(memorized[0].amount, Decimal('-30.00'))
        self.assertEqual(memorized[0].uamount, memorized[0].amount)
        self.assertEqual(memorized[0].payee, 'Big Box Store')
        self.assertEqual(memorized[0].category, 'Groceries')
        self.assertEqual(len(memorized[0].splits), 3)
        # TODO more tests of splits
        self.assertEqual(memorized[0].to_account, None)
        self.assertEqual(memorized[0].num_payments_done, None)
        self.assertEqual(memorized[0].memo, None)
        self.assertEqual(memorized[0].first_payment_date, None)
        self.assertEqual(memorized[0].address, None)
        self.assertEqual(memorized[0].years_of_loan, None)
        self.assertEqual(memorized[0].interests_rate, None)
        self.assertEqual(memorized[0].cleared, None)

        self.assertEqual(memorized[1]._mtype, 'P')
        self.assertEqual(memorized[1].amount, Decimal('-5.00'))
        self.assertEqual(memorized[1].uamount, memorized[1].amount)
        self.assertEqual(memorized[1].payee, 'Citi Cards')
        self.assertEqual(memorized[1].to_account, 'My Bank')
        self.assertFalse(memorized[1].splits)
        self.assertEqual(memorized[1].category, None)
        self.assertEqual(memorized[1].num_payments_done, None)
        self.assertEqual(memorized[1].memo, None)
        self.assertEqual(memorized[1].first_payment_date, None)
        self.assertEqual(memorized[1].years_of_loan, None)
        self.assertEqual(memorized[1].interests_rate, None)
        self.assertEqual(memorized[1].cleared, None)

        self.assertEqual(memorized[2]._mtype, 'P')
        self.assertEqual(memorized[2].amount, Decimal('-20000.00'))
        self.assertEqual(memorized[2].uamount, memorized[2].amount)
        self.assertEqual(memorized[2].payee, 'Fancy Car Dealer')
        self.assertEqual(memorized[2].category, 'Auto')
        self.assertFalse(memorized[2].splits)
        self.assertEqual(memorized[2].num_payments_done, None)
        self.assertEqual(memorized[2].to_account, None)
        self.assertEqual(memorized[2].memo, None)
        self.assertEqual(memorized[2].first_payment_date, None)
        self.assertEqual(memorized[2].years_of_loan, None)
        self.assertEqual(memorized[2].interests_rate, None)
        self.assertEqual(memorized[2].cleared, None)

        # KD        Deposit transaction
        self.assertEqual(memorized[3]._mtype, 'D')
        # Note, in the QIF file, this is written as 'T100,000.00', with the comma
        # This test confirms that it was parsed properly
        self.assertEqual(memorized[3].amount, Decimal('100000.00'))
        self.assertEqual(memorized[3].uamount, memorized[3].amount)
        self.assertEqual(memorized[3].payee, 'Opening Balance')
        self.assertEqual(memorized[3].memo, 'This may be written to the QIF with a comma')
        self.assertEqual(memorized[3].to_account, 'My Bank')
        self.assertFalse(memorized[3].splits)
        self.assertEqual(memorized[3].category, None)
        self.assertEqual(memorized[3].num_payments_done, None)
        self.assertEqual(memorized[3].first_payment_date, None)
        self.assertEqual(memorized[3].years_of_loan, None)
        self.assertEqual(memorized[3].interests_rate, None)
        self.assertEqual(memorized[3].cleared, None)

        self.assertEqual(memorized[4]._mtype, 'D')
        self.assertEqual(memorized[4].amount, Decimal('5.00'))
        self.assertEqual(memorized[4].uamount, memorized[4].amount)
        self.assertEqual(memorized[4].payee, 'Subway')
        self.assertEqual(memorized[4].memo, 'Test of using a tag')
        self.assertEqual(memorized[4].category, 'Dining/Sandwiches')
        self.assertFalse(memorized[4].splits)
        self.assertEqual(memorized[4].num_payments_done, None)
        self.assertEqual(memorized[4].to_account, None)
        self.assertEqual(memorized[4].first_payment_date, None)
        self.assertEqual(memorized[4].years_of_loan, None)
        self.assertEqual(memorized[4].interests_rate, None)
        self.assertEqual(memorized[4].cleared, None)

        self.assertEqual(memorized[5]._mtype, 'P')
        self.assertEqual(memorized[5].amount, Decimal('-45.00'))
        self.assertEqual(memorized[5].uamount, memorized[5].amount)
        self.assertEqual(memorized[5].payee, 'Sunoco')
        self.assertEqual(memorized[5].category, 'Auto:Gas')
        self.assertEqual(memorized[5].address, ['', '', '', '', '', ''])
        self.assertFalse(memorized[5].splits)
        self.assertEqual(memorized[5].num_payments_done, None)
        self.assertEqual(memorized[5].to_account, None)
        self.assertEqual(memorized[5].memo, None)
        self.assertEqual(memorized[5].first_payment_date, None)
        self.assertEqual(memorized[5].years_of_loan, None)
        self.assertEqual(memorized[5].interests_rate, None)
        self.assertEqual(memorized[5].cleared, None)


if __name__ == "__main__":
    import unittest
    unittest.main()
