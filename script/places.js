function getLocation(){
  navigator.geolocation.getCurrentPosition(near);
	function near(position){
    var store1v = 10.729218 + 106.695267
    var store2v = 10.784091 + 106.694368
    var location = position.coords.latitude + position.coords.longitude;
        if (Math.abs(location - store1v) > Math.abs(location - store2v))
        {
          document.getElementById("showNear").innerHTML="Store 2 is nearer to you";
        }
        else{
          document.getElementById("showNear").innerHTML="Store 1 is nearer to you";
        } 
      }
    }
// Code for the following using Google Maps API is based on examples from Google 	
function store1() {
  store = new google.maps.LatLng(10.729218,106.695267);
  var mapOptions = {
    center: store,
    zoom: 16,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
  };
  var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
  var marker = new google.maps.Marker({
    position: store,
    title:"First store"
  });
  marker.setMap(map);
  }
  google.maps.event.addDomListener(window, 'load', initialize);
	  
  function store2() {
  store = new google.maps.LatLng(10.784091,106.694368);
  var mapOptions = {
    center: store,
    zoom: 16,
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  var map = new google.maps.Map(document.getElementById("map-canvas"),mapOptions);
  var marker = new google.maps.Marker({
    position: store,
    title:"Second store"
  })
  marker.setMap(map);
  }
  google.maps.event.addDomListener(window, 'load', initialize);1