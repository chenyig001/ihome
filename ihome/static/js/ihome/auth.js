function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

// 页面加载请求用户实名信息
$(document).ready(function(){
    $.get("api/v1.0/user/auth", function(resp){
        if (resp.errno == "0"){
            var data = resp.data
            // 如果返回的数据中的real_name和id_card不null,表示用户有填写实名信息
            if (data.real_name && data.id_card){
                $("#real-name").val(data.real_name)
                $("#id-card").val(data.id_card)
                // 给input添加disabled属性，禁止用户修改
                $("#real-name").prop("disabled",true)
                $("#id-card").prop("disabled",true)
                // 隐藏提交保存按钮
                $("#form-auth .btn-success").hide()
            }

        }
        else if(resp.errno == "4101"){
            location.href="/login.html"
        }
        else{
            alert(resp.errmsg)
        }
    },"json")

    //保存用户实名信息
    $("#form-auth").submit(function(e){
        //禁止表单默认行为
        e.preventDefault()

        //如果用户没有填写完整，展示错误信息
        var real_name = $("#real-name").val()
        var id_card = $("#id-card").val()

        if (real_name =="" || id_card==""){
            $(".error-msg").show()
        }
        params = {
            real_name:real_name,
            id_card:id_card
        }
        json_data = JSON.stringify(params)
        //向后端发送请求
        $.ajax({
            url:"api/v1.0/user/auth",
            type:"post",
            data:json_data,
            contentType:"application/json",
            dataType:"json",
            headers:{
            "X-CSRFToken":getCookie("csrf_token")
             },success:function(resp){
                if (resp.errno=="0"){
                    $(".error-msg").hide()
                    //显示保存成功的提示信息
                    showSuccessMsg()
                    $("#real-name").prop("disabled",true)
                    $("#id-card").prop("disabled",true)
                    // 隐藏提交保存按钮
                    $("#form-auth .btn-success").hide()
                }
                else{
                    alert(resp.errmsg)
                }
             }
        })

    })
})






