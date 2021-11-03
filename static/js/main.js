$(document).ready(function () {
     listing()
})
function listing(){
    $.ajax({
       type: "GET",
       url: "/diary?sample_give=샘플데이터",
       data: {},
       success: function(response){
        alert(response['msg'])
       }
    })
}