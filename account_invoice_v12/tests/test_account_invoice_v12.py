# Copyright 2021 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.addons.mail.tests.test_mail_gateway import MAIL_MULTIPART_IMAGE


class TestAccountInvoiceV12(TransactionCase):
    at_install = False
    post_install = True

    def setUp(self):
        super(TestAccountInvoiceV12, self).setUp()
        # this is the text representation of a mail with three attachments
        # From: raoul@example.com, Subject={subject}, To: {to}
        self.mail_dict = self.env['mail.thread'].message_parse(
            MAIL_MULTIPART_IMAGE.format(
                subject='testmail for invoice import',
                to='invoice-via-mail@example.com',
            ),
        )
        self.journal = self.env['account.journal'].create({
            'name': 'testjournal',
            'type': 'purchase',
            'code': '42',
            # the local part of the mail above
            'alias_name': 'invoice-via-mail',
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'testsupplier',
            'supplier': True,
            # the from: address of the mail above
            'email': 'raoul@example.com',
        })

    def _import_invoice(self):
        return self.env['account.invoice'].browse(
            self.env['account.invoice'].message_new(self.mail_dict)
        )

    def _assert_things(self, invoice, supplier_email):
        self.assertTrue(invoice.exists())
        self.assertEqual(invoice.source_email, supplier_email),

    def test_01_happy_flow(self):
        """
        Test flow with all expected objects available in Odoo
        """
        invoice = self._import_invoice()
        self._assert_things(invoice, self.supplier.email)
        self.assertEqual(self.journal, invoice.journal_id)

    def test_02_missing_flow(self):
        """
        Test flow without expected objects available in Odoo
        """
        self.journal.unlink()
        self.supplier.unlink()
        invoice = self._import_invoice()
        self._assert_things(invoice, 'raoul@example.com')

    def test_03_forward_flow(self):
        """
        Test flow where a user forwards a supplier invoice
        """
        user = self.env['res.users'].create({
            'login': 'forwading_user',
            'partner_id': self.supplier.id,
        })
        user.supplier = False
        actual_supplier = self.env['res.partner'].create({
            'name': 'actual supplier',
            'email': 'actual_supplier@supplier.com',
        })
        self.mail_dict['body'] = 'This is from actual_supplier@supplier.com'
        invoice = self._import_invoice()
        self._assert_things(invoice, user.email)
        self.assertEqual(invoice.partner_id, actual_supplier)
