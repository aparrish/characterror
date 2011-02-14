class GameState(object):
	def __init__(self):
		self.manager = None

class GameStateManager(object):
	def __init__(self):
		self.states = list()
		self.muted_states = set()
	def add_state(self, state):
		self.states.append(state)
		state.manager = self
	def remove_state(self, state):
		assert state in self.states, "can't remove state that hasn't been added"
		self.states.remove(state)
	def draw(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'draw'):
				state.draw()
	def mouseClicked(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'mouseClicked'):
				state.mouseClicked()
	def keyPressed(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'keyPressed'):
				state.keyPressed()
	def mute(self, state):
		self.muted_states.add(state)
	def unmute(self, state):
		if state in self.muted_states:
			self.muted_states.remove(state)
	def remove_instances(self, classes):
		self.states = [state for state in self.states \
			if type(state) not in classes]
	def get_instances(self, classes):
		return [state for state in self.states if type(state) in classes]

class WatcherState(GameState):
	def mouseClicked(self):
		self.manager.add_state(StarfieldState())

class StarfieldState(GameState):
	def __init__(self):
		self.pts = list()
		for i in range(100):
			self.pts.append((random.randrange(800), random.randrange(600)))
	def draw(self):
		for pt in self.pts:
			stroke(255)
			point(pt[0], pt[1])
