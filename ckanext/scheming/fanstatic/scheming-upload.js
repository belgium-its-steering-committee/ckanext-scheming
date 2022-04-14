$(document).ready(function(){
    setTimeout(function(){
        $( "div[data-module-field_upload|='rtti_upload_doc']>div.form-group>label" ).text( $("div[data-module-field_upload|='rtti_upload_doc']" ).attr("data-module-upload_label") );
        $( "div[data-module-field_upload|='srti_upload_doc']>div.form-group>label" ).text( $("div[data-module-field_upload|='srti_upload_doc']" ).attr("data-module-upload_label") );
        $( "div[data-module-field_upload|='sstp_upload_doc']>div.form-group>label" ).text( $("div[data-module-field_upload|='sstp_upload_doc']" ).attr("data-module-upload_label") );
        $( "div[data-module-field_upload|='image_upload']>div.form-group>label" ).text( $("div[data-module-field_upload|='image_upload']" ).attr("data-module-upload_label") );
    },1000);
  });