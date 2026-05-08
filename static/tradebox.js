let global_mini_position_info = {}


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
  updatePositionsDisplay();
}, 2000);

// var refresh_option_positions_global_data = setInterval(function(){
//   updateOptionPositionsGlobalData();
// }, 5000);

var refresh_global_mini_position_info = setInterval(function(){
  updateGlobalMiniPositionInfo();
}, 5000);

function updateGlobalMiniPositionInfo() {
  $.get("/get_mini_position_info", function(data) {
    j_mini = JSON.parse(data)
    global_mini_position_info = j_mini;
  });
}

// HELPER FUNCTIONS
function updatePortfolioProfileDisplay(data) {
  html = "Value: " + data[1]['equity'] + " " + "Tradeable cash: " + data[1]['withdrawable_amount'];
  $('#portfolio_profile').html(html);
}

function updatePositionsDisplay() {
  // set all position-row spans
  // data-keep-alive to false
  $("span.position-row").attr("data-position-row-keep-alive", "false");

  for (let local_id in global_mini_position_info) {
    p_local_id = local_id
    p_unique_id = global_mini_position_info[local_id]['position_unique_id']
    p_option_id = global_mini_position_info[local_id]['option_unique_id']
    p_average_price = global_mini_position_info[local_id]['average_price']
    p_qty = global_mini_position_info[local_id]['qty']
    p_symbol = global_mini_position_info[local_id]['symbol']
    p_expiry = global_mini_position_info[local_id]['expiry']
    p_type = global_mini_position_info[local_id]['type']
    p_strike = global_mini_position_info[local_id]['strike']
    p_bid_size = global_mini_position_info[local_id]['bid_size']
    p_bid_price = global_mini_position_info[local_id]['bid_price']
    p_ask_size = global_mini_position_info[local_id]['ask_size']
    p_ask_price = global_mini_position_info[local_id]['ask_price']
    p_iv = global_mini_position_info[local_id]['iv']
    p_position_last_update_epoch_time = global_mini_position_info[local_id]['position_last_update_epoch_time']
    p_market_data_last_update_epoch_time = global_mini_position_info[local_id]['market_last_update_epoch_time']
    p_instrument_data_last_update_epoch_time = global_mini_position_info[local_id]['instrument_last_update_epoch_time']

    position_string = `<b>${p_local_id}</b> ${p_qty} ${p_average_price} ${p_symbol} ${p_type} ${p_strike} ${p_expiry}<br/>${p_bid_size}x<b>${p_bid_price}</b> ${p_ask_size}x<b>${p_ask_price}<b/> ${p_iv}<br/><br/>`

    // if div#position_display->span#position_unique_id exists
    // update that position_unique_id row with above data
    // each row has a checkbox with position_unique_id
    // $("[href='default.htm']")
    if ($(`span[data-position-html-unique-id="${p_unique_id}"]`).length >= 1) {
      $(`span[data-position-html-unique-id="${p_unique_id}"]`).html(position_string);
      $(`span[data-position-row-unique-id='${p_unique_id}']`).attr("data-position-row-keep-alive", "true");
    } else {
      // otherwise, create new row as span#position_unique_id
      // with new data
      $("#positions_container").append(`<span class="position-row" data-position-row-unique-id="${p_unique_id}" data-position-row-local-id="${p_local_id}" data-position-row-keep-alive="true"><input class="position-radio" type="radio" name="positions" data-position-radio-unique-id="${p_unique_id}" data-position-radio-local-id="${p_local_id}" /><span data-position-html-unique-id="${p_unique_id}" data-position-html-local-id="${p_local_id}">NOT GOOD><span data-position-last-epoch-update-position-unique-id="${p_unique_id}" data-position-last-update-epoch-time-local-id="${p_local_id}" data-position-last-update-epoch-time></span></span></span>`);
      $(`span[data-position-html-unique-id='${p_unique_id}']`).html(position_string);
    }
  }

  // delete all data-position-row spans
  // where data-keep-alive is false
  $('span[data-position-row-keep-alive="false"]').remove();
}

// function updateOptionPositionsGlobalData() {

//   // console.log("option_positions_global_data 1")
//   // console.log(option_positions_global_data)

//   // set keep_alive to false
//   for (let key in option_positions_global_data) {
//     // console.log(`position key: ${key}`)
//     // console.log(`keep_alive value at key #${key}: ${option_positions_global_data[key].keep_alive}`)
//     option_positions_global_data[key].keep_alive = false;
//   }

//   // console.log("option_positions_global_data 2")
//   // console.log(option_positions_global_data)

//   $.get("/get_open_option_positions", function(data) {
//     parsed_data = JSON.parse(data)
//     // console.log(`Retrieved position data: ${parsed_data}`)
//     // console.log("PARSED FRESH POSITION DATA")
//     // console.log(parsed_data)
    
//     parsed_data.forEach(function(pos) {
//       p_local_id = pos[4]
//       console.log(`p_local_id: ${p_local_id}`)
//       p_unique_id = pos[1]['option_id']
//       // console.log(`p_unique_id: ${p_unique_id}`)
//       p_position_info = pos[1]
//       // console.log(`p_position_info: ${p_position_info}`)

//       // console.log("1")
//       // console.log(option_positions_global_data[p_local_id])
//       // console.log("159")
//       // console.log(option_positions_global_data["159"])

//       if(!option_positions_global_data[p_local_id]) {
//         // console.log(`Position ${p_local_id} does not exist.`)
//         option_positions_global_data[p_local_id] = {};
//         option_positions_global_data[p_local_id].keep_alive = true;
//         option_positions_global_data[p_local_id].position_data = p_position_info;
//         option_positions_global_data[p_local_id].unique_id = p_unique_id;
//       } else {
//         // console.log(`Position ${p_local_id} does exist.`)
//         option_positions_global_data[p_local_id].keep_alive = true;
//         option_positions_global_data[p_local_id].position_data = p_position_info;
//         option_positions_global_data[p_local_id].unique_id = p_unique_id;
//       }
//     });

//     for (let key in option_positions_global_data) {
//       if (!option_positions_global_data[key].keep_alive) {
//         console.log(`Deleting position #${key}. keep_alive=${option_positions_global_data[key].keep_alive}`);
//         delete option_positions_global_data[key];
//       }
//     }
  
//   });

//   console.log("option_positions_global_data 3");
//   console.log(option_positions_global_data);
// }

// function updateOptionPositionsGlobalMarketData() {
//   option_uuids = new Array()
//   for (let key in option_positions_global_data) {
//     option_uuids.push(option_positions_global_data[key].unique_id);
//   }

//   $.get(`/get_open_option_position_market_data_by_id/${p_unique_id}`, function(data) {
//         market_data = JSON.parse(data);
//         console.log(`Market data for ${p_local_id}`)
//         console.log(market_data)
//         option_positions_global_data[p_local_id].market_data = market_data;
//       })
// }

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

function create_all_tables() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/create_all_tables');
  xhr.send(null);
}

function drop_all_tables() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/drop_all_tables');
  xhr.send(null);
}

function restart_server() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/restart_server');
  xhr.send(null);
}

function copyPositionCloseLinkToClipboard() {
  pos_local_id = $("input:radio[name='positions']:checked").attr("data-position-radio-local-id");
  navigator.clipboard.writeText(pos_local_id);
}