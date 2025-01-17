viewer.toolbarImages="static/img/toolbar"
viewer.toolbar = function(self) {
	var toolbar = document.createElement('div');
	toolbar.className='toolbar';
	
	var isEnterKey = function(event) {
		var keyCode;
		if(event.keyCode) // IE
			keyCode = event.keyCode, event.returnValue = false;
		else if(event.which) // Netscape/Firefox/Opera
			keyCode = event.which, event.preventDefault();
		return keyCode==13;
	}
	
	var zoomIn = document.createElement('img');
	zoomIn.className='toolbarButton';
	zoomIn.title='Zoom in';
	zoomIn.tabIndex="1";
	zoomIn.src=viewer.toolbarImages+'/in.png';
	zoomIn.onclick = zoomIn.onkeypress = function(event) {
		event=event?event:window.event;
		if (event.type == 'keypress') 
			if(!isEnterKey(event))
				return;
		var frameDimension = self.getFrameDimension();
		self.zoomTo(self.getZoomLevel()+1, frameDimension[0]/2,frameDimension[1]/2);
	}
	
	var zoomOut = document.createElement('img');
	zoomOut.className='toolbarButton';
	zoomOut.title='Zoom out';
	zoomOut.tabIndex="1";
	zoomOut.src=viewer.toolbarImages+'/out.png';
	zoomOut.onclick = zoomOut.onkeypress = function(event) {
		event=event?event:window.event;
		if (event.type == 'keypress') 
			if(!isEnterKey(event))
				return;
		
		var frameDimension = self.getFrameDimension();
		self.zoomTo(self.getZoomLevel()-1, frameDimension[0]/2,frameDimension[1]/2);
	}
	
	var center = document.createElement('img');
	center.className='toolbarButton';
	center.title='Center image';
	center.tabIndex="1";
	center.src=viewer.toolbarImages+'/center.png';
	center.onclick = center.onkeypress = function(event) {
		event=event?event:window.event;
		if (event.type == 'keypress') 
			if(!isEnterKey(event))
				return;
		self.reset();
	}
	
	var help = document.createElement('img');
	help.className='toolbarButton';
	help.tabIndex="1";
	help.src=viewer.toolbarImages+'/help.png';
	var helpText = document.createElement('div');
	helpText.className='helpText';
	helpText.style.display='none';
	helpText.innerHTML = '<h5 style="color:#40C0FF; font-size:12px; margin:2px 0;">How to use the image viewer?</h5>';
	helpText.innerHTML = helpText.innerHTML + "Zooming<hr> Use the mouse wheel or the toolbar to zoom in/out. You can also zoom IN using '+','x' or '=' keys and zoom OUT using '-' or 'z' keys using the keyboard.";
	helpText.innerHTML = helpText.innerHTML + "<br><br>Panning<hr> Click and drag the mouse to pan the image or use 'w','s','a' and 'd' keys for moving up,down,left and right respectively.<br>Alternatively you can use the arrow buttons to pan the image.";
	helpText.innerHTML = helpText.innerHTML + "<br><br>Center Image<hr> Click on the 'Center image' icon on the toolbar or press 'c' to center image.";
	
	help.onclick = help.onkeypress = function(event) {
		event=event?event:window.event;
		if (event.type == 'keypress') 
			if(!isEnterKey(event))
				return;
		if (helpText.style.display == 'none')
			helpText.style.display = 'block';
		else
			helpText.style.display = 'none';
	}
	
	var controls = document.createElement('img');
	controls.className='movement-controls';
	controls.src=viewer.toolbarImages+'/movement-controls.png';
	controls.useMap="#controls";
	var map = document.createElement('map');
	map.name="controls";
	
	var up=document.createElement('area');
	up.shape='rect';
	up.coords="17,1,31,17";
	up.style.cursor='pointer';
	up.onmousedown = function() {
		var dimension = self.getFrameDimension();
		self.moveBy(0,dimension[1]*0.1); //10%
	}
	map.appendChild(up);
	
	var down=document.createElement('area');
	down.shape='rect';
	down.coords="17,31,31,47";
	down.style.cursor='pointer';
	down.onmousedown = function() {
		var dimension = self.getFrameDimension();
		self.moveBy(0,-1*dimension[1]*0.1);
	}
	map.appendChild(down);
	
	var left=document.createElement('area');
	left.shape='rect';
	left.coords="1,17,17,31";
	left.style.cursor='pointer';
	left.onmousedown = function() {
		var dimension = self.getFrameDimension();
		self.moveBy(dimension[0]*0.1,0);
	}
	map.appendChild(left);
	
	var right=document.createElement('area');
	right.shape='rect';
	right.coords="31,17,47,31";
	right.style.cursor='pointer';
	right.onmousedown = function() {
		var dimension = self.getFrameDimension();
		self.moveBy(-1*dimension[0]*0.1,0);
	}
	map.appendChild(right);
	
	toolbar.appendChild(zoomIn);
	toolbar.appendChild(zoomOut);
	toolbar.appendChild(center);
	toolbar.appendChild(help);
	toolbar.appendChild(helpText);
	
	self.frameElement.appendChild(toolbar);
	self.frameElement.appendChild(controls);
	self.frameElement.appendChild(map);
}