function hrefBack() {
    history.go(-1);
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    //获取详情页面要展示的房屋编号
    var queryData = decodeQuery();
    var houseId = queryData["id"];

    //获取房屋的详细信息
    $.get("/api/v1.0/house/" + houseId, function(resp){
        if(resp.errno == "0"){
            var house = resp.data.house
            console.log(house)
            $(".swiper-container").html(template("house_image_template", {image_urls:resp.data.house.img_urls, price:resp.data.house.price}));
            $(".detail-con").html(template("house_detail_template", {house:resp.data.house}));

            // resp.user_id为访问页面用户，resp.house.house_id为房东
            if (resp.data.user_id != resp.data.house.user_id){
            $(".book-house").attr("href", "/booking.html?hid="+resp.data.house.house_id)
            $(".book-house").show();
           }

        var mySwiper = new Swiper ('.swiper-container', {
        loop: true,
        autoplay: 2000,
        autoplayDisableOnInteraction: false,
        pagination: '.swiper-pagination',
        paginationType: 'fraction'
       })
      }else{
        alert(resp.errmsg)
      }


    });



})