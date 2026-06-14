class State:
    def __init__(self, manager):
        self.manager = manager
        
    def finish(self, event: str = None):
        """Signal the manager that this state is complete."""
        self.manager.next_route(self, event)

    def update(self, dt):
        pass
        
    def draw(self, surface):
        pass
    
    def handle_event(self, event):
        pass
        
    def on_enter(self):
        pass
        
    def on_exit(self):
        pass

class StateManager:
    def __init__(self, audio_manager=None):
        self.stack = []
        self.router = None
        self.audio_manager = audio_manager
        
    def set_router(self, router):
        self.router = router
        if router:
            router.set_manager(self)

    def next_route(self, current_state: State, event: str = None):
        """Transition to the next state based on the router's map.
        
        Supports three route value types:
          1. A State class  → instantiated with (self,)
          2. A callable/lambda → called to produce a State instance
          3. A dict mapping event strings → class or callable
        """
        if not self.router:
            print("[StateManager] Warning: No router configured for next_route")
            return
            
        next_entry = self.router.get_next(current_state, event)
        if next_entry is None:
            print(f"[StateManager] Warning: No route found for {current_state.__class__.__name__} (event: {event})")
            return

        # If the route value is callable but NOT a class, it's a factory/lambda
        if callable(next_entry) and not isinstance(next_entry, type):
            next_state = next_entry(self)
        else:
            # It's a State class — instantiate it
            next_state = next_entry(self)

        self.set(next_state)

    def push(self, state):
        print(f"[DEBUG] StateManager: Pushing state {state.__class__.__name__}")
        if self.stack:
            self.stack[-1].on_exit()
        self.stack.append(state)
        state.on_enter()
        
    def pop(self):
        if self.stack:
            print(f"[DEBUG] StateManager: Popping state {self.stack[-1].__class__.__name__}")
            self.stack[-1].on_exit()
            self.stack.pop()
        if self.stack:
            print(f"[DEBUG] StateManager: Resuming state {self.stack[-1].__class__.__name__}")
            self.stack[-1].on_enter()
            
    def set(self, state):
        """Replaces the entire stack with a single state"""
        print(f"[DEBUG] StateManager: Setting state to {state.__class__.__name__}")
        while self.stack:
            self.stack[-1].on_exit()
            self.stack.pop()
        self.stack.append(state)
        state.on_enter()
        
    def update(self, dt):
        if self.stack:
            self.stack[-1].update(dt)
            
    def draw(self, surface):
        if self.stack:
            self.stack[-1].draw(surface)
            
    def handle_event(self, event):
        if self.stack:
            self.stack[-1].handle_event(event)

