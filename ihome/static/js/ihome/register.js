function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 保存图片验证码编号
var imageCodeId = "";

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    // 形成图片验证码的后端地址， 设置到页面中，让浏览请求验证码图片
    // 1. 生成图片验证码编号
    imageCodeId = generateUUID();
    // 是指图片url
    var url = "/api/v1.0/image_codes/" + imageCodeId;
    $(".image-code img").attr("src", url);
}

function sendSMSCode() {
    //点击发送短信验证码后被执行的函数
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }
     // ajax请求
    // /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
     var params = {
        image_code: imageCode,
        image_code_id: imageCodeId
    };
    $.get("/api/v1.0/sms_codes/"+mobile,params,function(resp){

        if (resp.errno == "0"){
        //表示发送成功
            var num = 60
            var timer = setInterval(function(){
                //修改倒计时文本
                if (num>1){
                    $(".phonecode-a").html(num+'秒');
                }
                else{
                     $(".phonecode-a").html('获取验证码 ');
                     $(".phonecode-a").attr("onclick", "sendSMSCode();");
                     clearInterval(timer)
                }
                num--;

            }, 1000,60)

        }else{
            alert(resp.errmsg)
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        }
    });

   }




$(document).ready(function() {
    // 页面加载获取图片验证码
    generateImageCode();
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });


    $(".form-register").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        phoneCode = $("#phonecode").val();
        passwd = $("#password").val();
        passwd2 = $("#password2").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        params = {
            mobile:mobile,
            sms_code:phoneCode,
            password:passwd,
            password2:passwd2
        }
        params = JSON.stringify(params);
//        $.post("/api/v1.0/users", params, headers=header, function(resp){
//               if (resp.errno=="0"){
//                    //注册成功
//                    location.href = '/index.html';
//               }
//               else{
//                    alert(resp.errmsg)
//               }
//        })
        $.ajax({
            url:"/api/v1.0/users",
            data:params,
            type:"post",
            contentType:"application/json",
            dataType:"json",
             headers:{
            "X-CSRFToken":getCookie("csrf_token")
             },
            success:function(resp){
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