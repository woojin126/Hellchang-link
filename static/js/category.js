$(function () {
        let data = window.location.pathname.replace("/category/", "")

        function showStar(data) {
        console.log(data)
          $.ajax({
              type: 'GET',
              url: '/api/sports',
              data: {
                  category:data
              },
              success: function (res) {
                  let List = res['result']
                  console.log(List)
                  cateGoryList(List)

              }
          });
        }
        function chageLang(data){
            let lang = ''
            if(data == 'baseball'){
                lang = '야구'
            }else if(data == 'baskball'){
               lang = '농구'
            }else{
                lang = '축구'
            }
            $('.lang').append(lang)
        }
        chageLang(data)
        showStar(data)

        function cateGoryList(List){
            let container = $('#pagination');
            container.pagination({
            dataSource: List,
            pageSize: 9,
            showPrevious: false,
            showNext: false,
            callback: function (data, pagination) {
                var dataHtml = '<ul class="videoCards">';
                $.each(data, function (index, item) {
                    let li = `<li class="videoCard">
                           <a href="/details/${item._id}">
                            <div class="thumbnail">
                                <img src='${item.image}'>
                            </div>
                            <div class="viedoTxt">
                                 <h4 class="title">${item.title}</h4>
                                 <div class="like">
                                    <i class="fas fa-heart"></i>
                                    <span class="num">${item.count_heart}</span>
                                 </div>
                            </div>
                           </a>
                          </li>`

                    dataHtml += li;
                });
                dataHtml += '</ul> ';

                $("#data-container").html(dataHtml);
            }
        })
        }
    })