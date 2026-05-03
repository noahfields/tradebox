option_positions_global_data = {};
option_positions_global_data = {
  "2": {
    "position_data": {},
    "market_data": {},
    "instrument_data": {},
    "keep_alive": true
  },
  "59": {
    "position_data": {},
    "market_data": {},
    "instrument_data": {},
    "keep_alive": true
  }
};

// REFRESH INTERVALS
var refresh_portfolio_profile = setInterval(function(){

  $.get("/portfolio_profile", function( data ) {
    data = JSON.parse(data);
    updatePortfolioProfileDisplay(data[0]);
  });

}, 5000); 

var refresh_all_runners_status = setInterval(function(){
  $.get("/get_all_runners_status", function( data ) {
    data = JSON.parse(data);
    data.forEach(updateRunnersStatus);
  });

}, 5000);

var refresh_positions_display = setInterval(function(){
  refreshPositionsDisplay();
}, 2000);

var refresh_option_positions_global_data = setInterval(function(){
  updateOptionPositionsGlobalData();
}, 5000);


// HELPER FUNCTIONS
function updatePortfolioProfileDisplay(data) {
  html = "Value: " + data[1]['equity'] + " " + "Tradeable cash: " + data[1]['withdrawable_amount'];
  $('#portfolio_profile').html(html);
}

function refreshPositionsDisplay() {
  for (const [key, value] of Object.entries(option_positions_global_data)) {
    position_unique_id = option_positions_global_data[key]['positions_data']['id']
    position_local_id = key
    position_symbol = option_positions_global_data[key]['position_data']['chain_symbol']
    position_expiry = option_positions_global_data[key]['position_data']['expiration_date']

    position_type = option_positions_global_data[key]['instrument_data']['type']
    position_strike = option_positions_global_data[key]['instrument_data']['strike_price']

    position_bid_size = option_positions_global_data[key]['market_data']['bid_size']
    position_bid_price = option_positions_global_data[key]['market_data']['bid_price']
    position_ask_size = option_positions_global_data[key]['market_data']['ask_size']
    position_ask_price = option_positions_global_data[key]['market_data']['ask_price']
    position_iv = option_positions_global_data[key]['market_data']['implied_volatility']

    position_string = position_local_id + ' ' + position_symbol + ' ' + position_type + ' ' + position_strike + ' ' + position_expiry + ' ' + position_bid_size + 'x' + position_bid_price + ' ' + position_ask_size + 'x' + position_ask_price + ' ' + position_iv;
    // each div#positions_container
    // has sub spans
    // that have data-position-local-id
    // and data-position-unique-id

    // set all position-row spans
    // data-keep-alive to false
    // ??????
    $(".position-row").attr("data-position-keep-alive", "false");

    // if div#position_display->span#position_unique_id exists
    // update that position_unique_id row with above data
    // each row has a checkbox with position_unique_id
    // $("[href='default.htm']")
    p_html_entry = $(`[data-position-html-unique-id=${position_unique_id}]`);
    if (p_html_entry.length) {
        p_html_entry.html = position_string;
        $(`.position-row-unique-id=${position_unique_id}`).attr("data-position-keep-alive", "true");
    } else {
      // otherwise, create new row as span#position_unique_id
      // with new data
      $("#positions_container").append(`<span class="position-row" data-position-row-unique-id="${position_unique_id}" data-position-row-local-id="${position_local_id}" data-position-keep-alive="true"><input type="checkbox" data-position-checkbox-unique-id="${position_unique_id}" data-position-checkbox-local-id="${position_local_id}" /><span data-position-html-unique-id="${position_unique_id}" data-position-html-local-id="${position_local_id}"></span></span>`);
      p_html_entry = $(`[data-position-html-unique-id=${position_unique_id}]`);
      p_html_entry.html = position_string;
    }

    // delete all data-position-row spans
    // where data-keep-alive is false
    // ??????
    $(`[data-position-keep-alive=false]`).remove();
  }
}

function updateOptionPositionsGlobalData(positions_data) {
  // console.log('starting update option positions global data');
  // console.log(option_positions_global_data);

  // set keep_alive to false
  for (const [key, value] of Object.entries(option_positions_global_data)) {
    option_positions_global_data[key]['keep_alive'] = false;
  }

  // get open option positions
  // loop through received option positions
  // set option_positions_global_data[local_id]
  // values
  // if that position exists in sotred global data
  // set keep_alive = true
  $.get("/get_open_option_positions", function(positions_data) {
    data = JSON.parse(positions_data);
    data.forEach(function(position_data) {
      console.log(position_data);
      local_id_key = position_data[0][4];
      option_positions_global_data[local_id_key][positions_data] = position_data[0][1];
      option_positions_global_data[local_id_key][keep_alive] = true;
    });
  });

  // delete unalive option positions from global data
  for (const [key, value] of Object.entries(option_positions_global_data)) {
    if (option_positions_global_data[key]['keep_alive'] == false) {
      delete option_positions_global_data[key];
    }
  }

  // get market data for each option in global data
  // get instrument data for each option in instrument data
  for (const [key, value] of Object.entries(option_positions_global_data)) {
    option_uuid = option_positions_global_data[key]['positions_data']['option_id'];

    $.get(`/get_open_option_position_market_data_by_id/${option_uuid}`, function(market_data) {
      market_data = JSON.parse(market_data);
      option_positions_global_data[key][market_data] = market_data;
    });

    $.get(`/get_open_option_position_instrument_data_by_id/${option_uuid}`, function(instrument_data) {
      instrument_data = JSON.parse(instrument_data);
      option_positions_global_data[key][instrument_data] = instrument_data;
    });
  }
}

function updateRunnersStatus(value, index, array) {
  // make sure display status components exist for this runner
  runner_name = value['runner_name_pk'];
  status_display_exists = $(`#runner_status_${runner_name}_active`).length
  if (! (status_display_exists)) {
    return;
  }

  // update display status components for this runner
  if (value['active'] == true) {
      $(`#runner_status_${runner_name}_active`).css('background-color', 'green');
  } else {
      $(`#runner_status_${runner_name}_active`).css('background-color', 'red');
  }

  if (value['current_update_success'] == true) {
      $(`#runner_status_${runner_name}_current_update_success`).css('background-color', 'green');
  } else {
      $(`#runner_status_${runner_name}_current_update_success`).css('background-color', 'red');
  }

  if (value['previous_update_success'] == true) {
      $(`#runner_status_${runner_name}_previous_update_success`).css('background-color', 'green');
  } else {
      $(`#runner_status_${runner_name}_previous_update_success`).css('background-color', 'red');
  }

  current_epoch_time = (Date.now() / 1000);
  runner_epoch_time = value['epoch_time_previous_success'];
  elapsed_time_since_last_update = current_epoch_time - runner_epoch_time;
  elapsed_boundary_time = value['adjusted_interval'] + 2;
  if (elapsed_time_since_last_update <= elapsed_boundary_time) {
      $(`#runner_status_${runner_name}_timeout`).css('background-color', 'green');
  } else {
      $(`#runner_status_${runner_name}_timeout`).css('background-color', 'red');
  }
}


function openTab(evt, tabName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

function install_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/install_runners');
  xhr.send(null);
}

function remove_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/remove_runners');
  xhr.send(null);
}

function enable_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/enable_runners');
  xhr.send(null);
}

function disable_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/disable_runners');
  xhr.send(null);
}

function start_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/start_runners');
  xhr.send(null);
}

function stop_runners() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/stop_runners');
  xhr.send(null);
}

function rh_login() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/rh_login');
  xhr.send(null);
}

function rh_logout() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/rh_logout');
  xhr.send(null);
}