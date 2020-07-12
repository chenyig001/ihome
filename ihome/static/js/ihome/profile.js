function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

//页面加载阻止表单默认提交行为
$(document).ready(function(){
    $("#form-avatar").submit(function(e){
        //阻止表单默认提交行为
        e.preventDefault();

        //利用jquery.form.min.js提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({
            url:"/api/v1.0/user/avatar",
            type:"post",
            dataType:"json",
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },success:function(resp){
                if (resp.errno=="0"){
                    var avatar_url = resp.data.avatar_url
                    $("#user-avatar").attr("src", avatar_url)
                }
                else{
                    alert(resp.errmsg)
                }

            }
        })
     })

         $("#form-name").submit(function(e){
            e.preventDefault();
            //获取表单输入的用户昵称
            user_name = $("#form-name #user-name").val()
            params = {user_name:user_name}
            data = JSON.stringify(params)
           $.ajax({
                url:"api/v1.0/user/user_name",
                type:"post",
                data:data,
                contentType:"application/json",
                dataType:"json",
                 headers:{
                "X-CSRFToken":getCookie("csrf_token")
                },success:function(resp){
                if (resp.errno=="0"){
                    $(".popup p").show()
                }
                else{
                     alert(resp.errmsg)
                }

                }
           })
        })



})

//$(document).ready(function(){
//
//})

