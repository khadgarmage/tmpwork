# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
from sqlalchemy import event
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model import make_timestamp
from pybossa.core import result_repo, db
from pybossa.model.project import Project
from pybossa.feed import update_feed
import json
    
@event.listens_for(TaskRun, 'after_insert')
def update_audit_data(mapper, conn, target):
    try:
        if not isinstance(target.info, dict):
            return
        data = target.info
        if not data.has_key('result'):
            return
        sql_query = ('select id from project where category_id in (select category_id \
            from project where id=%s) and id != %s') %  (target.project_id, target.project_id)
        print(sql_query)
        result = conn.execute(sql_query)
        print(3432432)
        one = result.fetchone()
        if len(one) <= 0:
            return
        project_id = one[0]
        print(one)
        info = {}
        print(target.__dict__)
        info['project_id'] = project_id
        info['task_id'] = target.task_id
        info['user_id'] = target.user_id
        info['user_ip'] = ""
        info['finish_time'] = target.finish_time
        info['result'] = data['result']
        info['answers'] = data['answers']
        info['question'] = data['question']
        info['link'] = data['link']
        info['url_m'] = data['url_m']
        info['url_b'] = data['url_b']
        sql_query = ("insert into task(created, project_id, state, quorum, calibration, \
            priority_0, info, n_answers) values (TIMESTAMP '%s', %s, 'ongoing', 0, 0, 0, '%s', 30) RETURNING id;" 
            % (make_timestamp(), project_id, json.dumps(info)))
        print(sql_query)
        result = conn.execute(sql_query)
        id_of_new_row = result.fetchone()[0]
        print(id_of_new_row) 
        sql_query = ("insert into counter(created, project_id, task_id, n_task_runs) \
             VALUES (TIMESTAMP '%s', %s, %s, 0)"
             % (make_timestamp(), project_id, id_of_new_row))
        print(sql_query) 
        conn.execute(sql_query)
        print(sql_query) 
        """Update PYBOSSA feed with new task."""
        sql_query = ('select name, short_name, info from project \
                     where id=%s') % project_id
        results = conn.execute(sql_query)
        obj = dict(action_updated='Task')
        tmp = dict()
        for r in results:
            tmp['id'] = project_id
            tmp['name'] = r.name
            tmp['short_name'] = r.short_name
            tmp['info'] = r.info
        tmp = Project().to_public_json(tmp)
        obj.update(tmp)
        update_feed(obj)
    except:
       raise