from odoo import fields, models, tools, api

class MRAssetReport(models.Model):
    """ MR Asset Report"""

    _name = "mr.asset.report"
    _auto = False
    _description = "Magnus - Asset Report"

    dep_year = fields.Char(string="Depreciation Year", readonly=True)
    code = fields.Char(string="Reference", readonly=True)
    name = fields.Char(string="Asset Name", readonly=True)
    profile_id = fields.Many2one('account.asset.profile', string='Profile', readonly=True)
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit', readonly=True)
    date_start = fields.Date(string='Asset Start Date', readonly=True)

    purchase_value = fields.Float(string='Purchase Value', readonly=True)
    new_purchase = fields.Float(string='New Purchase', readonly=True)
    start_value = fields.Float(string='Start Value', readonly=True)
    dep_value = fields.Float(string='Depreciation Value', readonly=True)
    end_value = fields.Float(string='End Value', readonly=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', readonly=True)


    state = fields.Selection(
            selection=[
                ('draft', 'Draft'),
                ('open', 'Running'),
                ('close', 'Close'),
                ('removed', 'Removed'),
            ], string='Asset Status', readonly=True)


    def _select(self):
        select_str = """ 
        select row_number() OVER () as id
            , d.dl_year as dep_year
            , a.code
            , a.name
            , case when extract(year from a.date_start)::text = dl_year then 0 
                else (case when init_val > 0 then init_val else end_value + dep_value end)
                end as start_value
            , dep_value
            , end_value
            , a.profile_id
            , a.operating_unit_id
            , a.purchase_value
            , a.date_start
            , a.company_id
            , case when extract(year from a.date_start)::text = dl_year then init_val else 0 end as new_purchase
            , a.state
        from 
        (
            select extract(year from dl.line_date)::text as dl_year
                   , coalesce(init_val, 0) as init_val
                   , round(coalesce(dep, 0) - coalesce(init_val, 0),2) as dep_value
                   , round(coalesce(dl.remaining_value, 0), 2) as end_value
                   , dl.asset_id
            from account_asset_line dl
            join (
                select distinct extract(year from line_date) as dl_year
                      , ( max(id) over (partition by extract(year from line_date), asset_id 
                                       order by extract(year from line_date))) as end_id
                      , ( sum(amount) over (partition by extract(year from line_date), asset_id 
                                       order by extract(year from line_date))) as dep
                      , asset_id
                from account_asset_line
            )e on e.end_id = dl.id and e.asset_id = dl.asset_id
            left outer join
            (
                select extract(year from line_date) as dl_year
                    , amount as init_val
                    , asset_id
                from account_asset_line l
                where l.type = 'create'
            )s on s.dl_year = e.dl_year and s.asset_id = e.asset_id
        )d
        join account_asset a on a.id = d.asset_id
        order by d.asset_id, d.dl_year
        
        """
        return select_str


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as ( %s)""" % (self._table, self._select())
        self.env.cr.execute(sql)
