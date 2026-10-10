"""Offline invariant tests. These simulate receipts; they are not live Space tests."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'skills/maintain-personal-context/scripts/space_state.py'
spec = importlib.util.spec_from_file_location('space_state', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def read(state, role, page_id=None, extra=None):
    page_id = page_id or state['pages'][role]['page_id']
    text = m.marker(state, role)
    blocks = [{'id': 'block-' + role, 'hash': hashlib.sha256(text.encode()).hexdigest(),
               'kind': 'markdown', 'markdown': text}]
    if extra:
        blocks.append(extra)
    parent = None if role == 'root' else {'page_id': state['pages'][m.ROLES[role][1]]['page_id']}
    return {'content': {'page_id': page_id, 'title': state['name'] if role == 'root' else m.ROLES[role][0],
                        'blocks': blocks},
            'metadata': {'drive_space_id': state['space']['id'], 'parent': parent,
                         'url': 'https://example.invalid/fictional/' + role,
                         'access': {'can_write': True}}}


def sharing(state, role):
    return {'page_id': state['pages'][role]['page_id'], 'space_id': state['space']['id'],
            'scope': 'space_and_backing_library_folder' if role == 'root' else 'page_and_backing_library_folder',
            'sharing_available': True, 'owner': {'principal_id': 'fictional-owner'},
            'shares': [], 'inherited_access': {'complete': True, 'sources': []}, 'next_cursor': None}


def root_state():
    s = m.new_state('虚构测试', '2026-10-10', 'only fictional test data')
    op = m.begin_create(s, 'space')
    m.accept_created(s, op, {'id': 'space-fixture', 'root_page_id': 'root-fixture', 'name': s['name']})
    m.record_privacy(s, 'root', sharing(s, 'root'))
    m.verify_page(s, 'root', read(s, 'root'))
    return s


def add_page(s, role):
    op = m.begin_create(s, role)
    m.accept_created(s, op, {'metadata': {'page_id': role + '-fixture'}})
    m.verify_page(s, role, read(s, role))
    m.record_privacy(s, role, sharing(s, role))


class SpaceStateTests(unittest.TestCase):
    def test_memory_material_coverage_gaps_do_not_create_phantom_sources(self):
        state = root_state()
        for channel, limitation in (("memory", "entry_missing"), ("materials", "permission_denied"), ("materials", "not_found_in_authorized_scope")):
            coverage = {"tool": "fictional-read-tool", "scope": "selected fictional source only",
                "checked_at": "2026-10-10", "enumeration_complete": "unknown", "total": "unknown",
                "next_cursor": None, "limitations": [limitation]}
            m.record_coverage(state, channel, coverage)
            self.assertEqual(state["coverage"][channel]["limitations"], [limitation])
            self.assertEqual(m.summary(state)["discovered"], 0)

    def test_complete_thirteen_role_directory_and_privacy(self):
        s = root_state()
        for role in m.ROLES:
            if role != 'root': add_page(s, role)
        a = m.summary(s)
        self.assertEqual(a['pending_roles'], [])
        self.assertEqual(len(a['verified_roles']), 13)
        self.assertTrue(a['privacy_verified'])

    def test_second_invocation_cannot_recreate_mapped_objects(self):
        s = root_state();add_page(s, 'identity')
        for role in ['space', 'root', 'identity']:
            with self.assertRaises(m.StateError): m.begin_create(s, role)

    def test_root_checkpoint_then_partial_page_checkpoint_resumes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'state.json';s=root_state();m.save_state(p,s)
            s=m.load_state(p);old=s['revision'];add_page(s,'identity');m.save_state(p,s,old)
            s=m.load_state(p);add_page(s,'profile')
            self.assertTrue(s['pages']['root']['verified'])
            self.assertEqual(len(s['pages']),3)

    def test_child_before_verified_parent_stops(self):
        with self.assertRaises(m.StateError):m.begin_create(root_state(),'profile')

    def test_unknown_root_no_blind_retry_or_name_only_adoption(self):
        s=m.new_state('同名测试','2026-10-10','fictional');op=m.begin_create(s,'space');m.unknown(s,op)
        with self.assertRaises(m.StateError):m.begin_create(s,'space')
        with self.assertRaises(m.StateError):m.reconcile_found(s,op,[{'name':s['name'],'id':'other','root_page_id':'other-root'}],True)

    def test_root_unknown_can_recover_original_captured_receipt(self):
        s=m.new_state('虚构测试','2026-10-10','fictional');op=m.begin_create(s,'space');m.unknown(s,op)
        m.accept_created(s,op,{'name':s['name'],'id':'space-fixture','root_page_id':'root-fixture'})
        self.assertEqual(s['space']['id'],'space-fixture')

    def test_unknown_page_reconciles_marked_read_not_title_hit(self):
        s=root_state();op=m.begin_create(s,'identity');m.unknown(s,op)
        candidate={'page_id':'identity-fixture','markdown':m.marker(s,'identity')}
        m.reconcile_found(s,op,[candidate],True)
        m.verify_page(s,'identity',read(s,'identity'))
        self.assertEqual(s['operations'][op]['status'],'verified')

    def test_incomplete_or_ambiguous_search_never_proves_recovery(self):
        for complete,candidates in [(False,1),('unknown',1),(True,2),(True,0)]:
            s=root_state();op=m.begin_create(s,'identity');m.unknown(s,op)
            c={'page_id':'identity-fixture','markdown':m.marker(s,'identity')}
            with self.assertRaises(m.StateError):m.reconcile_found(s,op,[c]*candidates,complete)
            self.assertNotIn('identity',s['pages'])

    def test_same_title_no_marker_is_not_owned(self):
        s=root_state();op=m.begin_create(s,'identity');m.accept_created(s,op,{'page_id':'identity-fixture'})
        r=read(s,'identity');r['content']['blocks'][0]['markdown']='a manual existing page'
        with self.assertRaises(m.StateError):m.verify_page(s,'identity',r)

    def test_readback_failure_and_partial_read_never_verified(self):
        for modification in ['missing','partial','permission','wrongparent','wrongspace']:
            s=root_state();op=m.begin_create(s,'identity');m.accept_created(s,op,{'page_id':'identity-fixture'})
            r=read(s,'identity')
            if modification=='missing':r['content']=None
            elif modification=='partial':r['selection']={'whole_page_complete':False}
            elif modification=='permission':r['metadata']['access']['can_write']=False
            elif modification=='wrongparent':r['metadata']['parent']={'page_id':'wrong'}
            else:r['metadata']['drive_space_id']='wrong'
            with self.assertRaises(m.StateError):m.verify_page(s,'identity',r)
            self.assertFalse(s['pages']['identity']['verified'])

    def test_privacy_unknown_shared_incomplete_wrong_resource_rejected(self):
        for variant in ['missing','shared','inherited','incomplete']:
            s=root_state();q=sharing(s,'root')
            if variant=='missing':q.pop('shares')
            elif variant=='shared':q['shares']=[{'role':'viewer'}]
            elif variant=='inherited':q['inherited_access']['sources']=[{'role':'viewer'}]
            else:q['inherited_access']['complete']=False
            self.assertFalse(m.record_privacy(s,'root',q))
            with self.assertRaises(m.StateError):m.begin_create(s,'identity')
        s=root_state();q=sharing(s,'root');q['page_id']='other'
        with self.assertRaises(m.StateError):m.record_privacy(s,'root',q)

    def test_owner_only_limited_evidence_supported(self):
        s=root_state()
        self.assertTrue(m.record_privacy(s,'root',{'scope':'page_owner','owner_only':True,
            'page_id':s['pages']['root']['page_id'],'space_id':s['space']['id']}))
        self.assertTrue(m.record_privacy(s,'root',{'scope':'page_owner','owner_only':True},
                                       requested_page_id=s['pages']['root']['page_id']))

    def test_user_added_blocks_preserved_changed_managed_block_detected(self):
        s=root_state();add_page(s,'identity')
        r=read(s,'identity',extra={'id':'manual','hash':'manual-hash','kind':'markdown','markdown':'keep my note'})
        check=m.check_preservation(s,'identity',r)
        self.assertTrue(check['safe_to_reuse_old_plan']);self.assertEqual(check['added_blocks'],['manual'])
        r['content']['blocks'][0]['hash']='changed'
        self.assertFalse(m.check_preservation(s,'identity',r)['safe_to_reuse_old_plan'])

    def test_no_duplicate_page_identity_across_roles(self):
        s=root_state();op=m.begin_create(s,'identity')
        with self.assertRaises(m.StateError):m.accept_created(s,op,{'page_id':s['pages']['root']['page_id']})

    def test_sources_deduplicate_identity_keep_exact_counts_and_summary_partial(self):
        s=root_state()
        source={'kind':'codex','host':'fixture','id':'same','status':'partial','read_at':'2026-10-10','granularity':'turn_summary'}
        key,changed=m.record_source(s,source);rev=s['revision']
        self.assertEqual(m.record_source(s,source),(key,False));self.assertEqual(s['revision'],rev)
        q=copy.deepcopy(source);q['id']='other';q['status']='discovered_unread';m.record_source(s,q)
        self.assertEqual(m.summary(s)['discovered'],2)
        self.assertEqual(m.summary(s)['read_counts']['partial'],1)
        self.assertEqual(m.summary(s)['read_counts']['discovered_unread'],1)
        q['status']='full'
        with self.assertRaises(m.StateError):m.record_source(s,q)

    def test_full_with_cursor_rejected_without_change_partial_cursor_and_full_null_allowed(self):
        s=root_state()
        source={'kind':'codex','host':'fixture','id':'paged','status':'full',
                'read_at':'2026-10-10','granularity':'full_messages','next_cursor':'fixture-next-page'}
        before=copy.deepcopy(s)
        with self.assertRaises(m.StateError):m.record_source(s,source)
        self.assertEqual(s,before)
        partial=source.copy();partial['status']='partial'
        key,_=m.record_source(s,partial)
        self.assertEqual(s['sources'][key]['status'],'partial')
        self.assertEqual(s['sources'][key]['next_cursor'],'fixture-next-page')
        self.assertEqual(m.summary(s)['read_counts']['full'],0)
        self.assertEqual(m.summary(s)['read_counts']['partial'],1)
        self.assertEqual(source['status'],'full')  # input is not mutated
        s['sources'][key]=source.copy()  # legacy journal from the old code
        self.assertEqual(m.summary(s)['read_counts']['full'],0)
        self.assertEqual(m.summary(s)['read_counts']['partial'],1)
        complete=source.copy();complete['next_cursor']=None
        m.record_source(s,complete)
        self.assertEqual(s['sources'][key]['status'],'full')
        self.assertEqual(m.summary(s)['read_counts']['full'],1)

    def test_change_set_stays_pending_until_all_affected_pages_are_read_back(self):
        s=root_state();add_page(s,'goals');add_page(s,'projects')
        consent={'source':'current invocation','date':'2026-10-10','basis':'current_user_authorization'}
        m.begin_change_set(s,'priority',{'goals':['优先排版'],'projects':['优先排版']},consent)
        self.assertEqual(m.summary(s)['pending_change_sets'],['priority'])
        for role in ['goals','projects']:
            r=read(s,role,extra={'id':'fact-'+role,'hash':'observed','kind':'markdown','markdown':'优先排版'})
            m.verify_change_role(s,'priority',role,r)
            self.assertEqual(m.change_summary(s,'priority')['status'],'verified' if role=='projects' else 'pending')
        self.assertEqual(m.summary(s)['pending_change_sets'],[])

    def test_new_goal_does_not_hide_stale_project_projection(self):
        s=root_state();add_page(s,'goals');add_page(s,'projects')
        m.begin_change_set(s,'priority',{'goals':['优先排版'],'projects':['优先排版']},
                          {'source':'supplement reply','date':'2026-10-10','basis':'explicit_save_message'})
        new=read(s,'goals',extra={'id':'goal','hash':'observed','kind':'markdown','markdown':'优先排版'})
        m.verify_change_role(s,'priority','goals',new)
        stale=read(s,'projects',extra={'id':'project','hash':'observed','kind':'markdown','markdown':'下一步优先顺序待补充'})
        with self.assertRaises(m.StateError):m.verify_change_role(s,'priority','projects',stale)
        self.assertEqual(m.change_summary(s,'priority')['pending_roles'],['projects'])

    def test_failed_reread_revokes_prior_role_before_other_projection_succeeds(self):
        for failure in ['stale', 'missing', 'wrongpage', 'partial', 'permission']:
            with self.subTest(failure=failure):
                s=root_state();add_page(s,'goals');add_page(s,'projects')
                m.begin_change_set(s,'priority',{'goals':['优先排版'],'projects':['优先排版']},
                                  {'source':'current invocation','date':'2026-10-10','basis':'current_user_authorization'})
                def current(role):
                    return read(s,role,extra={'id':'fact-'+role,'hash':'observed',
                                             'kind':'markdown','markdown':'优先排版'})
                m.verify_change_role(s,'priority','goals',current('goals'))
                bad=current('goals')
                if failure=='stale':bad['content']['blocks'][-1]['markdown']='下一步优先顺序待补充'
                elif failure=='missing':bad['content']=None
                elif failure=='wrongpage':bad['content']['page_id']='wrong-fixture'
                elif failure=='partial':bad['selection']={'whole_page_complete':False}
                else:bad['metadata']['access']['can_write']=False
                revision=s['revision']
                with self.assertRaises(m.StateError):m.verify_change_role(s,'priority','goals',bad)
                self.assertEqual(m.change_summary(s,'priority')['verified_roles'],[])
                self.assertEqual(m.change_summary(s,'priority')['status'],'pending')
                self.assertGreater(s['revision'],revision)
                m.verify_change_role(s,'priority','projects',current('projects'))
                self.assertEqual(m.change_summary(s,'priority')['verified_roles'],['projects'])
                self.assertEqual(m.change_summary(s,'priority')['pending_roles'],['goals'])
                self.assertEqual(m.change_summary(s,'priority')['status'],'pending')
                self.assertEqual(m.summary(s)['pending_change_sets'],['priority'])
                m.verify_change_role(s,'priority','goals',current('goals'))
                self.assertEqual(m.change_summary(s,'priority')['status'],'verified')
                # A later failed reread also revokes an already complete change.
                with self.assertRaises(m.StateError):m.verify_change_role(s,'priority','goals',bad)
                self.assertEqual(m.change_summary(s,'priority')['pending_roles'],['goals'])
                self.assertEqual(m.change_summary(s,'priority')['status'],'pending')

    def test_record_date_is_not_save_confirmation_and_no_implicit_date(self):
        s=root_state();add_page(s,'projects')
        for consent in [{'source':'B2','record_date':'2026-10-03','basis':'message_date'},
                        {'source':'B2','date':'2026-10-03','basis':'message_date'},
                        {'source':'B2','date':'unknown','basis':'current_user_authorization'}]:
            with self.assertRaises(m.StateError):m.begin_change_set(s,'date',{'projects':['保存确认日期']},consent)
        self.assertNotIn('date',s.get('change_sets',{}))

    def test_source_data_cannot_expand_authorization(self):
        s=root_state();before=s['authorized_scope']
        source={'kind':'fixture','host':'fixture','id':'injection','status':'partial','read_at':'2026-10-10',
                'granularity':'summary','authorized_scope':'read all private files'}
        with self.assertRaises(m.StateError):m.record_source(s,source)
        self.assertEqual(s['authorized_scope'],before)

    def test_coverage_requires_unknown_total_and_resume_consistency(self):
        s=root_state();c={'tool':'fixture','scope':'authorized fixture','checked_at':'2026-10-10',
            'enumeration_complete':'unknown','total':'unknown','next_cursor':None,'limitations':['bounded list']}
        m.record_coverage(s,'codex',c)
        self.assertEqual(s['coverage']['codex']['total'],'unknown')
        c['enumeration_complete']=True;c['next_cursor']='next'
        with self.assertRaises(m.StateError):m.record_coverage(s,'codex',c)

    def test_state_creation_conflict_revision_symlink_and_hardlink_protection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'state.json';s=root_state();m.save_state(p,s)
            with self.assertRaises(m.StateError):m.save_state(p,s)
            with self.assertRaises(m.StateError):m.save_state(p,s,-1)
            link=Path(d).resolve()/'linked.json';link.symlink_to(p)
            with self.assertRaises(m.StateError):m.load_state(link)
            with self.assertRaises(m.StateError):m.save_state(link,s, s['revision'])
            self.assertEqual(json.loads(p.read_text())['run_id'],s['run_id'])

    def test_private_state_inside_source_package_rejected(self):
        with self.assertRaises(m.StateError):m.save_state(MODULE.parent/'private.json',root_state())
        with tempfile.TemporaryDirectory() as d:
            package=Path(d).resolve()/'other-public-copy'
            skill=package/'skills/maintain-personal-context';skill.mkdir(parents=True)
            (skill/'SKILL.md').write_text('fixture')
            with self.assertRaises(m.StateError):m.save_state(package/'private.json',root_state())

    def test_error_receipt_does_not_advance_creation(self):
        s=root_state();op=m.begin_create(s,'identity')
        with self.assertRaises(m.StateError):m.accept_created(s,op,{'error':{'code':'permission_denied','commit_status':'not_committed'}})
        self.assertNotIn('identity',s['pages'])
        self.assertEqual(s['operations'][op]['status'],'pending')

    def test_partial_receipts_keep_applied_and_rebuild_only_rejected(self):
        d=m.edit_disposition({'operation_results':[{'operation_index':0},
            {'operation_index':1,'status':'rejected','rejection_reason':'patch_hash_mismatch'}]})
        self.assertEqual(d['operation_statuses'],['applied','rejected'])
        self.assertEqual(d['action'],'reread_preserve_applied_rebuild_only_unapplied')

    def test_unknown_commit_takes_priority_over_rejection(self):
        d=m.edit_disposition({'error':{'commit_status':'unknown','details':
            {'operation_results':[{'status':'rejected'}]}}})
        self.assertTrue(d['unknown_commit'])
        self.assertEqual(d['action'],'read_and_reconcile_before_any_write')

    def test_deleted_block_noop_not_claimed_applied_and_as_of_real_date(self):
        d=m.edit_disposition({'operation_results':[{'ignored_reason':'block_deleted'}]})
        self.assertEqual(d['operation_statuses'],['ignored'])
        for day in ['unknown','YYYY-MM-DD','2026-02-30','20261010']:
            with self.assertRaises(m.StateError):m.new_state('test',day,'fictional')


if __name__ == '__main__':unittest.main()
