$(document).ready(function(){
    // 调用实名认证接口
    $.get("/api/v1.0/user/auth", function(resp){
        if (resp.errno == "0"){
            if(resp.data.real_name!=null && resp.data.id_card!=null){
                 $(".auth-warn").hide();
                  $(".new-house").show();
            }
            else{
            $(".auth-warn").show();
            $(".new-house").hide();
          }
        }

    });


    $.get("/api/v1.0/house/info", function(resp){
        if (resp.errno == "0"){
            var houses = resp.data.houses
            console.log(houses)
            // 使用js模板
            var html = template("house-template", {houses:houses})
            $("#houses-list").append(html)
        }
        else{
            var html = template("house-template", {houses:[]})
            $("#houses-list").html(html)
        }
    })

})