//  hide not founded images
function bind_img_error() {
  $("img").on('error', function() {
    $(this).hide();
  });
}

function toggle_social_hub(paper_pk, media) {

  // Bind collapse
  $('.paper-' + paper_pk + ' .social .content .collapse.' + media).one('shown.bs.collapse', function() {
    $('.paper-' + paper_pk + ' .social .next').show();
  });

  $('.paper-' + paper_pk + ' .social .content .collapse.' + media).one('hidden.bs.collapse', function() {
    $('.paper-' + paper_pk + ' .social .next').hide();
  });

  // change class for Button
  $('.paper-' + paper_pk + ' .social button:not(.' + media + ')').removeClass('active');
  $('.paper-' + paper_pk + ' .social button .' + media).toggleClass('active');
  // toggle div
  $('.paper-' + paper_pk + ' .social .content .collapse:not(.' + media + ')').collapse('hide');
  $('.paper-' + paper_pk + ' .social .content .collapse.' + media).collapse('toggle');
  // remove button



}



// TODO merge this functions
function toggle_twitter(paper_pk) {
  toggle_social_hub(paper_pk, 'twitter');
  if ($('.paper-' + paper_pk + ' .social .content .twitter').children().length == 0) {
    next_page_twitter(paper_pk, 1);
  }

}

function next_page_twitter(paper_pk, page) {
  $.ajax({
    url: url_twitter,
    data: {
      'paper_pk': paper_pk,
      'page': page,
      'count': 10
    },
    contentType: 'application/x-www-form-urlencoded',
    dataType: 'json',
    type: 'POST',
    success: function(data) {
      if (data.status == 'ok') {
        $('.paper-' + paper_pk + ' .social .content .twitter').append(data.content);
        if (data.has_next) {
          $('.paper-' + paper_pk + ' .social .next').html('<a href="javascript:next_page_twitter(\'' + paper_pk + '\',' + (data.number + 1) + ');">Next</a>')
        }

      }
    }
  });
}

function toggle_reddit(paper_pk) {
  toggle_social_hub(paper_pk, 'reddit');
}

function update_user(user_info) {
  $('#library-count-badge').text(user_info.library_count)
}

function login(event) {
  event.preventDefault();
  $.ajax({
    url: url_login,
    data: $('#form').serialize(),
    contentType: 'application/x-www-form-urlencoded',
    dataType: 'json',
    type: 'POST',
    success: function(data) {
      if (data.status == "ok") {
        location.reload(true);
      } else {
        $("#password").addClass("form-control-danger");
        $("#password-div").addClass("has-danger");
      }
    }
  });
}

function logout(event) {
  // event.preventDefault();
  $.ajax({
    url: url_logout,
    contentType: 'application/x-www-form-urlencoded',
    type: 'POST',
    success: function(data) {
      /* beautify preserve:start */
          location.replace(url_index);
          /* beautify preserve:end */
    }
  });
}

function hide_content() {
  var loading = $('<div id="loading" class="align-items-center d-flex" hidden><i class="my-auto mx-auto fa fa-spinner fa-spin fa-3x fa-fw"></i></div>');
  $('body').append(loading);
  $('#loading').fadeTo(400, 1.0);

}


function show_content() {
  $('#loading').fadeTo(400, 0.0, function() {
    this.remove();
  });
}

function update_navbar(query) {
  $('#navbar-sort-group a').removeClass('active');
  if ('sort' in query) {
    if (query['sort'] == 'relevance') {
      $('#navbar-sort-group a.sort-relevance').addClass('active')
    }
    if (query['sort'] == 'date') {
      $('#navbar-sort-group a.sort-date').addClass('active')
    }
    if (query['sort'] == 'twitter') {
      $('#navbar-sort-group a.sort-twitter').addClass('active')
    }
    if (query['sort'] == 'library') {
      $('#navbar-sort-group a.sort-library').addClass('active')
    }
  }

  if ('group' in query) {
    if (query['group'] == 'd') {
      $('#navbar-sort-group a.group-d').addClass('active')
    }
    if (query['group'] == 'w') {
      $('#navbar-sort-group a.group-w').addClass('active')
    }
    if (query['group'] == 'm') {
      $('#navbar-sort-group a.group-m').addClass('active')
    }
    if (query['group'] == 'y') {
      $('#navbar-sort-group a.group-y').addClass('active')
    }
  } else {
    $('#navbar-sort-group a.group-a').addClass('active')
  }

  // only show valid sort/group options
  if(query.sort == 'relevance' || query.sort == 'date'){
    $('.group').fadeOut();
  }
  else{
    $('.group').fadeIn();
  }
  if(!query.q){
    $('.sort-relevance').fadeOut();

  }
  else{
    $('.sort-relevance').fadeIn();

  }
}


function load_index(base_query, update) {
  var _query = $.extend({}, base_query);
  console.log(JSON.stringify(_query));
  console.log(JSON.stringify(update));

  var query_changed = false;
  for (var key in update) {
    if (key in _query) {
      if (_query[key] == update[key]) {
        continue;
      }
    }
    query_changed = true;
    _query[key] = update[key];

  }
  console.log(_query);

  // TODO
  if(!query_changed){
    //nothing todo
    return;
  }
  //TODO more logic
  next_page_number = 2;
  next_page_content = null;
  // $('#list-view').append(next_page_content)

  hide_content();

  $.ajax({
    url: url_index,
    data: {
      'query': JSON.stringify(_query)
    },
    contentType: 'application/x-www-form-urlencoded',
    dataType: 'json',
    type: 'POST',
    success: function(data) {


      if (data.status == "ok") {
        update_navbar(data.query);
        $('#list-view').html(data.content);
        query = data.query;

        console.log(data.query);
      }
      show_content();
    }
  });
}
