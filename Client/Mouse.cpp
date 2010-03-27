#include "Game.h"

Mouse::Mouse()
{
	Mx = 0;
	My = 0;
}

void Mouse::Draw(SDL_Surface *Dest)
{
	Sprite::Draw(Dest, Game::GetInstance().Sprites[SPRID_CURSOR], Mx, My, SPRID_CURSOR_ARROW);
}

void Mouse::OnEvent(SDL_Event *EventSource)
{
	Event::OnEvent(EventSource);
}

void Mouse::OnMouseMove(int X, int Y, int RelX, int RelY, bool Left, bool Right, bool Middle)
{
	Mx = X;
	My = Y;
}