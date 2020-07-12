function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {

    mobile = getCookie("mobile")
    $("#mobile").val(mobile)

    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
    // 禁止表单默认提交行为
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        //session["mobile"]=mobile
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        //组装参数
        params = {
            mobile:mobile,
            password:passwd
        }
        // 转换json格式
        data = JSON.stringify(params)
        // ajax请求
        $.ajax({
            url:"/api/v1.0/session",
            data:data,
            type:"post",
            contentType:"application/json",
            dataType:"json",
            headers:{
            "X-CSRFToken":getCookie("csrf_token")
            },success:function(resp){
                if (resp.errno=="0"){
                 //注册成功
                        location.href = '/index.html';
                   }
                   else{
                        alert(resp.errmsg)
                   }
            }
        })

    });
})