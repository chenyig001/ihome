// 获取浏览器csrf_token
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
//    $.get("/api/logout", function(data){
//        if (0 == data.errno) {
//            location.href = "/";
//        }
//    })
        $.ajax({
            url:"api/v1.0/session",
            type:"delete",
            dataType:"json",
            headers:{
            "X-CSRFToken":getCookie("csrf_token")
             },success:function(resp){
                if (resp.errno=="0"){
                    location.href="/";
                }
             }
        })
}

$(document).ready(function(){

    $.ajax({
            url:"api/v1.0/user/info",
            type:"get",
            dataType:"json",
            success:function(resp){
                if (resp.errno=="0"){
                    $("#user-avatar").attr("src", resp.data.avatar)
                    $(".menu-text #user-name").html(resp.data.name)
                    $(".menu-text #user-mobile").html(resp.data.mobile)
                }
                else{
                    alert(resp.errmsg)
                }
             }
        })
})