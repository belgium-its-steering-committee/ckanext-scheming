# encoding: utf-8
import cgi
import logging
import os
import datetime
import mimetypes
import ckan.lib.munge as munge
import ckan.logic as logic
import ckan.plugins as plugins

from ckan.lib.uploader import get_storage_path
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from ckan.common import config


ALLOWED_UPLOAD_TYPES = (cgi.FieldStorage, FlaskFileStorage)
MB = 1 << 20

log = logging.getLogger(__name__)
log.warning("GEO----> CHILD uploader.py")

_storage_path = None
_max_resource_size = None
_max_image_size = None


def _copy_file(input_file, output_file, max_size):
    log.warning("GEO----> |++in <copy_file> functie")
    input_file.seek(0)
    current_size = 0
    while True:
        current_size = current_size + 1
        # MB chunks
        data = input_file.read(MB)

        if not data:
            break
        output_file.write(data)
        if current_size > max_size:
            raise logic.ValidationError({'upload': ['File upload too large']})


def _get_underlying_file(wrapper):
    log.warning("GEO----> ||+in <get_underlying_file> functie")
    if isinstance(wrapper, FlaskFileStorage):
        log.warning("GEO----> ||+ => returned wrapper.stream")
        return wrapper.stream
    log.warning("GEO----> ||+  => returned wrapper.file")
    return wrapper.file


def _make_dirs_if_not_existing(storage_path):
    try:
        os.makedirs(storage_path)
    except OSError as e:
        # errno 17 is file already exists
        if e.errno != 17:
            raise


class OrganizationUploader(object):
    def __init__(self, object_type, old_filename=None):
        """ Setup upload by creating a subdirectory of the storage directory
        of name object_type. old_filename is the name of the file in the url
        field last time"""
        log.warning("GEO---->///in <organisationUploader> class")
        log.warning("GEO----> |+INFO: self object type is : " + "xxxx")
        log.warning("GEO----> |+INFO: object_type is : " + object_type)

        self.storage_path = None
        self.filename = None
        self.filepath = None
        path = get_storage_path()
        log.debug("storage base path check: " + path)
        if not path:
            return
        self.storage_path = os.path.join(path, 'storage', 'uploads', 'organization')
        log.debug("storage path for self: " + self.storage_path)
        _make_dirs_if_not_existing(self.storage_path)
        self.object_type = object_type
        self.old_filename = old_filename
        self.old_filepath = None

        # hack into this to upload NAP DOC
        # SSTP
        self.sstp_doc_url = ''
        self.sstp_doc_clear = None
        self.sstp_doc_file_field = None
        self.sstp_doc_upload_field_storage = None
        self.sstp_doc_filename = None
        self.sstp_doc_filepath = None
        self.sstp_doc_tmp_filepath = None
        self.sstp_doc_upload_file = None
        self.sstp_doc_old_filename = None
        self.sstp_doc_old_filepath = None
        # SRTI
        self.srti_doc_url = ''
        self.srti_doc_clear = None
        self.srti_doc_file_field = None
        self.srti_doc_upload_field_storage = None
        self.srti_doc_filename = None
        self.srti_doc_filepath = None
        self.srti_doc_tmp_filepath = None
        self.srti_doc_upload_file = None
        self.srti_doc_old_filename = None
        self.srti_doc_old_filepath = None
        # RTTI
        self.rtti_doc_url = ''
        self.rtti_doc_clear = None
        self.rtti_doc_file_field = None
        self.rtti_doc_upload_field_storage = None
        self.rtti_doc_filename = None
        self.rtti_doc_filepath = None
        self.rtti_doc_tmp_filepath = None
        self.rtti_doc_upload_file = None
        self.rtti_doc_old_filename = None
        self.rtti_doc_old_filepath = None
        # end hack

    def update_data_dict(self, data_dict, url_field, file_field, clear_field):
        """ Manipulate data from the data_dict.  url_field is the name of the
        field where the upload is going to be. file_field is name of the key
        where the FieldStorage is kept (i.e the field where the file data
        actually is). clear_field is the name of a boolean field which
        requests the upload to be deleted.  This needs to be called before
        it reaches any validators"""
        log.warning("GEO---->///IN <UPDATE_DATA_DICT> def")
        log.warning("GEO----> |+INFO: Self object.type is: " + self.object_type)
        log.warning("GEO----> |+INFO: url_field is: " + url_field)
        log.warning("GEO----> |+INFO: inkomende paramater file_field is: " + file_field)
        log.warning("GEO----> |+INFO: clear_field is: " + clear_field)
        self.url = data_dict.get(url_field, '')
        self.clear = data_dict.pop(clear_field, None)
        self.file_field = file_field
        self.upload_field_storage = data_dict.pop(file_field, None)

        if not self.storage_path:
            return

        # hack into this to upload NAP DOC
        # SSTP
        log.warning("GEO----> +++in <data_dict SSTP> functie")
        if self.sstp_doc_old_filename:
            self.sstp_doc_old_filepath = os.path.join(self.storage_path, data_dict.get('name'), self.sstp_doc_old_filename)

        self.sstp_doc_clear = data_dict.pop('sstp_clear_upload_doc', None)
        self.sstp_doc_file_field = 'sstp_upload_doc'
        self.sstp_doc_upload_field_storage = data_dict.pop(self.sstp_doc_file_field, None)
        if isinstance(self.sstp_doc_upload_field_storage, (ALLOWED_UPLOAD_TYPES)):
            log.warning("GEO----> |++in <data dict SSTP> instance")
            self.sstp_doc_filename = self.sstp_doc_upload_field_storage.filename
            self.sstp_doc_filename = munge.munge_filename(self.sstp_doc_filename)
            organization_storagepath = os.path.join(self.storage_path, data_dict.get('name'))
            _make_dirs_if_not_existing(organization_storagepath)
            self.sstp_doc_filepath = os.path.join(organization_storagepath, self.sstp_doc_filename)
            data_dict['sstp_doc_document_upload'] = self.sstp_doc_filename
            data_dict['url_type'] = 'upload'
            self.sstp_doc_upload_file = _get_underlying_file(self.sstp_doc_upload_field_storage)
            self.sstp_doc_tmp_filepath = self.sstp_doc_filepath + '~'
        # keep the file if there has been no change
        elif self.sstp_doc_old_filename and not self.sstp_doc_old_filename.startswith('http'):
            if not self.sstp_doc_clear:
                data_dict['sstp_doc_document_upload'] = self.sstp_doc_old_filename
            if self.sstp_doc_clear and self.sstp_doc_url == self.sstp_doc_old_filename:
                data_dict['sstp_doc_document_upload'] = ''
        log.warning("GEO----> |___uit <data_dict SSTP> functie")

        # SRTI
        log.warning("GEO----> +++in <data dict SRTI> functie")
        if self.srti_doc_old_filename:
            self.srti_doc_old_filepath = os.path.join(self.storage_path, data_dict.get('name'),
                                                 self.srti_doc_old_filename)
        self.srti_doc_clear = data_dict.pop('srti_clear_upload_doc', None)
        self.srti_doc_file_field = 'srti_upload_doc'
        self.srti_doc_upload_field_storage = data_dict.pop(self.srti_doc_file_field, None)
        if isinstance(self.srti_doc_upload_field_storage, (ALLOWED_UPLOAD_TYPES)):
            log.warning("GEO----> |++in <data dict SRTI> instance")
            self.srti_doc_filename = self.srti_doc_upload_field_storage.filename
            self.srti_doc_filename = munge.munge_filename(self.srti_doc_filename)
            organization_storagepath = os.path.join(self.storage_path, data_dict.get('name'))
            _make_dirs_if_not_existing(organization_storagepath)
            self.srti_doc_filepath = os.path.join(organization_storagepath, self.srti_doc_filename)
            data_dict['srti_doc_document_upload'] = self.srti_doc_filename
            data_dict['url_type'] = 'upload'
            self.srti_doc_upload_file = _get_underlying_file(self.srti_doc_upload_field_storage)
            self.srti_doc_tmp_filepath = self.srti_doc_filepath + '~'
        # keep the file if there has been no change
        elif self.srti_doc_old_filename and not self.srti_doc_old_filename.startswith('http'):
            if not self.srti_doc_clear:
                data_dict['srti_doc_document_upload'] = self.srti_doc_old_filename
            if self.srti_doc_clear and self.srti_doc_url == self.srti_doc_old_filename:
                data_dict['srti_doc_document_upload'] = ''
        log.warning("GEO----> |___uit <data_dict SRTI> functie")

        # RTTI
        log.warning("GEO----> +++in <data_dict RRTI> functie")
        if self.rtti_doc_old_filename:
            log.warning("GEO----> in<OLD FILENAME> = TRUE dus data_dict(rrti_doc_file_field, none) -> breekt _get_underlying file")
            self.rtti_doc_old_filepath = os.path.join(self.storage_path, data_dict.get('name'), self.rtti_doc_old_filename)
            self.rtti_doc_clear = data_dict.pop('rtti_clear_upload_doc', None)
            self.rtti_doc_file_field = 'rtti_upload_doc'
            self.rtti_doc_upload_field_storage = data_dict.pop(self.rtti_doc_file_field, None)
        if isinstance(self.rtti_doc_upload_field_storage, (ALLOWED_UPLOAD_TYPES)):
            log.warning("GEO----> in <data_dict RRTI> instance")
            self.rtti_doc_filename = self.rtti_doc_upload_field_storage.filename
            self.rtti_doc_filename = munge.munge_filename(self.rtti_doc_filename)
            organization_storagepath = os.path.join(self.storage_path, data_dict.get('name'))
            _make_dirs_if_not_existing(organization_storagepath)
            self.rtti_doc_filepath = os.path.join(organization_storagepath, self.rtti_doc_filename)
            data_dict['rtti_doc_document_upload'] = self.rtti_doc_filename
            data_dict['url_type'] = 'upload'
            self.rtti_doc_upload_file = _get_underlying_file(self.rtti_doc_upload_field_storage)
            self.rtti_doc_tmp_filepath = self.rtti_doc_filepath + '~'
        # keep the file if there has been no change
        elif self.rtti_doc_old_filename and not self.rtti_doc_old_filename.startswith('http'):
            log.warning("GEO----> in <data_dict RRTI BESTAANDE> functie")
            if not self.rtti_doc_clear:
                data_dict['rtti_doc_document_upload'] = self.rtti_doc_old_filename
            if self.rtti_doc_clear and self.rtti_doc_url == self.rtti_doc_old_filename:
                data_dict['rtti_doc_document_upload'] = ''
        # end NAP DOC hack
        log.warning("GEO----> |___uit <data_dict RRTI> functie")

        log.warning("GEO----> +++in <data_dict Algemeen> functie")
        if self.old_filename:
            log.warning("GEO----> self.old_filename wordt aangepast L211")
            self.old_filepath = os.path.join(self.storage_path, data_dict.get('name'), self.old_filename)

        if isinstance(self.upload_field_storage, (ALLOWED_UPLOAD_TYPES)):
            log.warning("GEO----> in <data_dict Algemeen> instance")
            self.filename = self.upload_field_storage.filename
            self.filename = munge.munge_filename(self.filename)
            organization_storagepath = os.path.join(self.storage_path, data_dict.get('name'))
            _make_dirs_if_not_existing(organization_storagepath)
            self.filepath = os.path.join(organization_storagepath, self.filename)
            data_dict[url_field] = self.filename
            data_dict['url_type'] = 'upload'
            self.upload_file = _get_underlying_file(self.upload_field_storage)
            self.tmp_filepath = self.filepath + '~'
        # keep the file if there has been no change
        elif self.old_filename and not self.old_filename.startswith('http'):
            if not self.clear:
                data_dict[url_field] = self.old_filename
            if self.clear and self.url == self.old_filename:
                data_dict[url_field] = ''
        log.warning("GEO----> |___uit <data_dict Algemeen> functie")
        log.warning("GEO---->///UIT <UPDATE_DATA_DICT> def")

    def upload(self, max_size=2):
        """ Actually upload the file.
        This should happen just before a commit but after the data has
        been validated and flushed to the db. This is so we do not store
        anything unless the request is actually good.
        max_size is size in MB maximum of the file"""
        
        log.warning("GEO---->///IN <UPLOAD> def")
        log.warning("GEO----> +++in <upload> Algemeen functie")
        if self.filename:
            with open(self.tmp_filepath, 'wb+') as output_file:
                log.warning("GEO --> |++in <upload> Algemeen try")
                try:
                    _copy_file(self.upload_file, output_file, max_size)
                except logic.ValidationError:
                    os.remove(self.tmp_filepath)
                finally:
                    self.upload_file.close()
            os.rename(self.tmp_filepath, self.filepath)
            self.clear = True

        if (self.clear and self.old_filename
                and not self.old_filename.startswith('http')):
            try:
                os.remove(self.old_filepath)
            except OSError:
                pass
        log.warning("GEO----> |___uit <upload> Algemeen functie")

        # hack into this to upload NAP DOC
        # SSTP
        log.warning("GEO----> +++in <upload> SSTP functie")
        if self.sstp_doc_filename:
            with open(self.sstp_doc_tmp_filepath, 'wb+') as output_file:
                log.warning("GEO----> |++in <Upload> SSTP try")
                try:
                    _copy_file(self.sstp_doc_upload_file, output_file, max_size)
                except logic.ValidationError:
                    os.remove(self.sstp_doc_tmp_filepath)
                    raise
                finally:
                    self.sstp_doc_upload_file.close()
            os.rename(self.sstp_doc_tmp_filepath, self.sstp_doc_filepath)
            self.sstp_doc_clear = True

        if (self.sstp_doc_clear and self.sstp_doc_old_filename
                and not self.sstp_doc_old_filename.startswith('http')):
            try:
                os.remove(self.sstp_doc_old_filepath)
            except OSError:
                pass
        log.warning("GEO----> |___uit <upload> SSTP functie")

        # SRTI
        log.warning("GEO----> +++in <upload> SRTI functie")
        if self.srti_doc_filename:
            with open(self.srti_doc_tmp_filepath, 'wb+') as output_file:
                log.warning("GEO----> |++in <Upload> SRTI try")
                try:
                    _copy_file(self.srti_doc_upload_file, output_file, max_size)
                except logic.ValidationError:
                    os.remove(self.srti_doc_tmp_filepath)
                    raise
                finally:
                    self.srti_doc_upload_file.close()
            os.rename(self.srti_doc_tmp_filepath, self.srti_doc_filepath)
            self.srti_doc_clear = True

        if (self.srti_doc_clear and self.srti_doc_old_filename
                and not self.srti_doc_old_filename.startswith('http')):
            try:
                os.remove(self.srti_doc_old_filepath)
            except OSError:
                pass
        log.warning("GEO----> |___uit <upload> SRTI functie")

        # RTTI
        log.warning("GEO----> +++in <upload> RRTI functie")
        if self.rtti_doc_filename:
            with open(self.rtti_doc_tmp_filepath, 'wb+') as output_file:
                log.warning("GEO----> |++in <Upload> RTTI try")
                try:
                    _copy_file(self.rtti_doc_upload_file, output_file, max_size)
                except logic.ValidationError as e:
                    os.remove(self.rtti_doc_tmp_filepath)
                finally:
                    self.rtti_doc_upload_file.close()
            os.rename(self.rtti_doc_tmp_filepath, self.rtti_doc_filepath)
            self.rtti_doc_clear = True

        if (self.rtti_doc_clear and self.rtti_doc_old_filename
                and not self.rtti_doc_old_filename.startswith('http')):
            try:
                os.remove(self.rtti_doc_old_filepath)
            except OSError:
                pass
        log.warning("GEO----> |___uit <upload> RRTI functie")
        log.warning("GEO---->///UIT <UPLOAD> def")
        # end hack

