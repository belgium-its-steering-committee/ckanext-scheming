# encoding: utf-8

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h
from ckan.lib.plugins import lookup_group_plugin
from ckan.lib.plugins import lookup_group_controller
import ckan.model as model
from ckan.common import OrderedDict, c, config, request
import ckan.lib.search as search
import ckan.logic as logic
import ckan.lib.base as base
import logging

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
render = base.render
abort = base.abort
log = logging.getLogger(__name__)

class customGroupOrganization(base.BaseController):
    
    group_types = ['organization']
    
    def _setup_template_variables(self, context, data_dict, group_type=None):
        if 'type' not in data_dict:
            data_dict['type'] = group_type
        return lookup_group_plugin(group_type).\
            setup_template_variables(context, data_dict)
    
    def _group_form(self, group_type=None):
        return lookup_group_plugin(group_type).group_form()

    def _ensure_controller_matches_group_type(self, id):
        group = model.Group.get(id)
        if group is None:
            abort(404, _('Group not found'))
        if group.type not in self.group_types:
            abort(404, _('Incorrect group type'))
        return group.type

    def _new_template(self, group_type):
        return lookup_group_plugin(group_type).new_template()
    
    def _edit_template(self, group_type):
        return lookup_group_plugin(group_type).edit_template()
    
    # end hooks
    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return string

    def _action(self, action_name):
        ''' select the correct group/org action '''
        return get_action(self._replace_group_org(action_name))
    
    def _check_access(self, action_name, *args, **kw):
        ''' select the correct group/org check_access '''
        return check_access(self._replace_group_org(action_name), *args, **kw)
    
    def _guess_group_type(self, expecting_name=False):
        """
            Guess the type of group from the URL.
            * The default url '/group/xyz' returns None
            * group_type is unicode
            * this handles the case where there is a prefix on the URL
              (such as /data/organization)
        """
        parts = [x for x in request.path.split('/') if x]

        idx = -1
        if expecting_name:
            idx = -2

        gt = parts[idx]

        return gt

    def _check_access(self, action_name, *args, **kw):
        ''' select the correct group/org check_access '''
        return check_access(self._replace_group_org(action_name), *args, **kw)
    
    # customization
    def new(self, data=None, errors=None, error_summary=None):
            log.warning("GEO---->///PLUGIN: in <new group>")
            if data and 'type' in data:
                group_type = data['type']
            else:
                group_type = self._guess_group_type(True)
            if data:
                data['type'] = group_type

            context = {'model': model, 'session': model.Session,
                    'user': c.user,
                    'save': 'save' in request.params,
                    'parent': request.params.get('parent', None)}
            try:
                self._check_access('organization_create', context)
            except NotAuthorized:
                abort(403, _('Unauthorized to create a group'))

            if context['save'] and not data and request.method == 'POST':
                return self._save_new(context, group_type)

            data = data or {}
            if not data.get('image_url', '').startswith('http'):
                data.pop('image_url', None)

            errors = errors or {}
            error_summary = error_summary or {}
            vars = {'data': data, 'errors': errors,
                    'error_summary': error_summary, 'action': 'new',
                    'group_type': group_type}

            self._setup_template_variables(context, data, group_type=group_type)
            c.form = render(self._group_form(group_type=group_type),
                            extra_vars=vars)
            return render(self._new_template(group_type),
                        extra_vars={'group_type': group_type})

    def edit(self, id, data=None, errors=None, error_summary=None):
            log.warning("GEO---->///PLUGIN <edit group>")
            group_type = self._ensure_controller_matches_group_type(
                id.split('@')[0])

            context = {'model': model, 'session': model.Session,
                    'user': c.user,
                    'save': 'save' in request.params,
                    'for_edit': True,
                    'parent': request.params.get('parent', None)
                    }
            data_dict = {'id': id, 'include_datasets': False}

            if context['save'] and not data and request.method == 'POST':
                old_data = self._action('organization_show')(context, data_dict)
                rttiBool=(not old_data['rtti_doc_document_upload'] == request.params['rtti_doc_document_upload'])
                srtiBool =(not old_data['srti_doc_document_upload'] == request.params['srti_doc_document_upload'])
                sstpBool =(not old_data['sstp_doc_document_upload'] == request.params['sstp_doc_document_upload'])
                imageBool =(not old_data['image_url'] == request.params['image_url'])
                return self._save_edit(id, context, rttiBool, srtiBool, sstpBool, imageBool)
                #return self._save_edit(id, context)

            try:
                log.warning("GEO----> +++ IN <_edit> _edit TRY")
                data_dict['include_datasets'] = False
                old_data = self._action('organization_show')(context, data_dict)
                c.grouptitle = old_data.get('title')
                c.groupname = old_data.get('name')
                data = data or old_data
            except (NotFound, NotAuthorized):
                abort(404, _('Organization not found'))

            group = context.get("group")
            c.group = group
            c.group_dict = self._action('organization_show')(context, data_dict)

            try:
                self._check_access('organization_update', context)
            except NotAuthorized:
                abort(403, _('User %r not authorized to edit %s') % (c.user, id))

            errors = errors or {}
            vars = {'data': data, 'errors': errors,
                    'error_summary': error_summary, 'action': 'edit',                                                       
                    'group_type': group_type}
            
            self._setup_template_variables(context, data, group_type=group_type)
            c.form = render(self._group_form(group_type), extra_vars=vars)

            return render(self._edit_template(c.group.type),
                        extra_vars={'group_type': group_type})

    def _save_new(self, context, group_type=None):
        log.warning("GEO---->///PLUGIN: <_save_new group>")
        try:
            #log.warning("GEO----> +++ in <Try>")
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.params))))
            data_dict['type'] = group_type or 'group'
            context['message'] = data_dict.get('log_message', '')
            data_dict['users'] = [{'name': c.user, 'capacity': 'admin'}]
            group = self._action('organization_create')(context, data_dict)
            # Redirect to the appropriate _read route for the type of group
            h.redirect_to(group['type'] + '_read', id=group['name'])
            
        except (NotFound, NotAuthorized) as e:
            abort(404, _('Group not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            log.warning("GEO----> +++ in <validation error>")
            if data_dict.get('url_type') == 'upload':
                data_dict['url_type']=''
                data_dict['previous_upload']=True
                data_dict['image_url']=''
                data_dict['sstp_doc_document_upload']=''
                data_dict['srti_doc_document_upload']=''
                data_dict['rtti_doc_document_upload']=''
        return self.new(data_dict, errors, error_summary)

    '''
    def _force_reindex(self, grp):
             When the group name has changed, we need to force a reindex                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
            of the datasets within the group, otherwise they will stop
            appearing on the read page for the group (as they're connected via
            the group name)
            group = model.Group.get(grp['name'])
            for dataset in group.packages():
                search.rebuild(dataset.name)
    '''

    def _save_edit(self, id, context, rttiBool, srtiBool, sstpBool, imageBool):
        log.warning("GEO---->///PLUGIN <save_edit group>")
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id
            context['allow_partial_update'] = True
            group = self._action('organization_update')(context, data_dict)
            if id != group['name']:
                self._force_reindex(group)
            
            h.redirect_to('%s_read' % group['type'], id=group['name'])
        except (NotFound, NotAuthorized) as e:
            abort(404, _('Organization not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            if data_dict.get('url_type') == 'upload':
                data_dict['url_type']=''
                data_dict['previous_upload']=True
                data_dict['image_url']='' if imageBool else data_dict['image_url']
                data_dict['rtti_doc_document_upload'] ='' if rttiBool else data_dict['rtti_doc_document_upload']
                data_dict['sstp_doc_document_upload']='' if sstpBool else data_dict['sstp_doc_document_upload']
                data_dict['srti_doc_document_upload']='' if srtiBool else data_dict['srti_doc_document_upload']
        
        return self.edit(id, data_dict, errors, error_summary)


