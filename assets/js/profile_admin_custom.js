// document status changes collapsed, can be expanded
(function($) {
	$(document).ready(function() {
		var selector = "h2:contains('Document status changes')";
		$(selector).parent().addClass("collapsed");
		$(selector).append(" (<a class=\"collapse-toggle\" id=\"customcollapser\" href=\"#\"> Show </a>)");
		$("#customcollapser").click(function() {
		    $(selector).parent().toggleClass("collapsed");
		});
	})
})(django.jQuery);


(function($) {
	$(document).ready(function() {

		    $('#id_passport_reason').parent().attr('hidden', true)
		$('#id_proof_of_residence_reason').parent().attr('hidden', true)
		    $('#id_send_passport_mail').parent().attr('hidden', true)
		    $('#id_send_proof_of_residence_mail').parent().attr('hidden', true)

		$('#id_passport_state').change(function(){
			if ($('#id_passport_state :selected').text() === 'failed') {
				$('#id_passport_reason').parent().attr('hidden', false)
				$('#id_send_passport_mail').parent().attr('hidden', false)
			}else{
				if ($('#id_passport_state :selected').text() === 'verified'){
		    			$('#id_send_passport_mail').parent().attr('hidden', false)
				}else{
					$('#id_send_passport_mail').parent().attr('hidden', true)
				};
				$('#id_passport_reason').parent().attr('hidden', true)
			}
		});

		$('#id_proof_of_residence_state').change(function(){
			if ($('#id_proof_of_residence_state :selected').text() === 'failed') {
				$('#id_proof_of_residence_reason').parent().attr('hidden', false)
	 		    $('#id_send_proof_of_residence_mail').parent().attr('hidden', false)
			}else{
				if ($('#id_proof_of_residence_state :selected').text() === 'verified'){
		    			$('#id_send_proof_of_residence_mail').parent().attr('hidden', false)
				}else{
					$('#id_send_proof_of_residence_mail').parent().attr('hidden', true)
				};
				$('#id_proof_of_residence_reason').parent().attr('hidden', true)
			}
		});

	})
})(django.jQuery);